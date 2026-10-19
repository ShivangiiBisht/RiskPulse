"""Module A - tactical, event-driven index rebalancer.

For every rebalance step the engine:
  1. time-decays and aggregates signal sentiment per stock (shrunk toward 0 so one headline can't dominate),
  2. adds CONTAGION: a high-impact shock at one stock spills over to its same-sector peers,
  3. adds a MARKET effect from macro / geopolitical signals, scaled by each sector's beta,
  4. detects the RISK REGIME (NORMAL / ELEVATED / CRISIS) and tilts away from high-beta names (risk-off),
  5. maps scores to weights with min/max bounds and a turnover cap to avoid whipsaw.
"""
import math
from bisect import bisect_left
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta

from app.db import list_signals
from app.engine.scoring import MARKET
from app.entities import TICKER_ALIASES, beta_of, peers_of, sector_of

HALF_LIFE_HOURS = 12.0
WINDOW = timedelta(hours=HALF_LIFE_HOURS * 6)
PRIOR = 1.0               # shrinkage: sentiment = sum(s*w) / (sum(w) + PRIOR)
TILT_K = 2.5              # sentiment -> log-weight sensitivity
MIN_MULT, MAX_MULT = 0.4, 2.0   # weight bounds as a multiple of the equal weight
TURNOVER_CAP = 0.15       # max one-way turnover per rebalance
CONTAGION_LAMBDA = 0.4
CONTAGION_IMPACT_MIN = 7
MARKET_EFFECT = 0.5
RISK_OFF = 1.0
STRESS_NORM = 2.0
REGIME_ELEVATED, REGIME_CRISIS = 0.25, 0.55


@dataclass
class Sig:
    entity: str
    ts: datetime
    sentiment: float
    quality: float          # confidence * credibility
    impact: int
    event_type: str
    snippet: str
    provider: str


def load_signals(limit: int = 20000) -> list[Sig]:
    rows = list_signals(limit=limit, newest_first=False)
    return [
        Sig(
            entity=row["entity"],
            ts=datetime.fromisoformat(row["timestamp"]),
            sentiment=row["sentiment"],
            quality=row["confidence"] * row["credibility"],
            impact=row["impact"],
            event_type=row["event_type"],
            snippet=row["text_snippet"],
            provider=row["provider"],
        )
        for row in rows
    ]


def regime_of(stress_index: float) -> str:
    if stress_index >= REGIME_CRISIS:
        return "CRISIS"
    if stress_index >= REGIME_ELEVATED:
        return "ELEVATED"
    return "NORMAL"


def _bound_and_normalise(raw: dict[str, float], base: float) -> dict[str, float]:
    total = sum(raw.values())
    weights = {t: w / total for t, w in raw.items()}
    low, high = MIN_MULT * base, MAX_MULT * base
    for _ in range(25):
        clipped = {t: min(max(w, low), high) for t, w in weights.items()}
        total = sum(clipped.values())
        weights = {t: w / total for t, w in clipped.items()}
        if all(low - 1e-9 <= w <= high + 1e-9 for w in weights.values()):
            break
    return weights


def _apply_turnover_cap(target: dict[str, float], prev: dict[str, float]) -> tuple[dict, float]:
    turnover = 0.5 * sum(abs(target[t] - prev[t]) for t in target)
    if turnover <= TURNOVER_CAP:
        return target, turnover
    step = TURNOVER_CAP / turnover
    return {t: prev[t] + (target[t] - prev[t]) * step for t in target}, TURNOVER_CAP


def snapshot(active: list[Sig], now: datetime, prev: dict[str, float]) -> dict:
    tickers = list(TICKER_ALIASES)
    base = 1 / len(tickers)
    num, den = defaultdict(float), defaultdict(float)
    max_impact: dict[str, int] = defaultdict(int)
    drivers: dict[str, list] = defaultdict(list)
    stress_sum = 0.0

    for sig in active:
        decay = 0.5 ** ((now - sig.ts).total_seconds() / 3600 / HALF_LIFE_HOURS)
        weight = sig.quality * decay
        num[sig.entity] += sig.sentiment * weight
        den[sig.entity] += weight
        if decay > 0.25:
            max_impact[sig.entity] = max(max_impact[sig.entity], sig.impact)
        if sig.impact >= 6 and sig.sentiment < 0:
            stress_sum += (sig.impact - 5) / 5 * -sig.sentiment * decay
        drivers[sig.entity].append((sig.sentiment * weight, sig))

    own = {t: num[t] / (den[t] + PRIOR) for t in tickers}
    market = num[MARKET] / (den[MARKET] + PRIOR)
    stress_index = 1 - math.exp(-stress_sum / STRESS_NORM)

    rows, raw = {}, {}
    for ticker in tickers:
        shocked_peers = [p for p in peers_of(ticker) if max_impact[p] >= CONTAGION_IMPACT_MIN]
        contagion = CONTAGION_LAMBDA * (
            sum(own[p] for p in shocked_peers) / len(shocked_peers) if shocked_peers else 0.0
        )
        market_effect = MARKET_EFFECT * market * beta_of(ticker)
        effective = max(-1.0, min(1.0, own[ticker] + contagion + market_effect))
        raw[ticker] = base * math.exp(
            TILT_K * effective - RISK_OFF * stress_index * (beta_of(ticker) - 0.9)
        )
        top = sorted(drivers[ticker], key=lambda item: abs(item[0]), reverse=True)[:3]
        rows[ticker] = {
            "ticker": ticker,
            "sector": sector_of(ticker),
            "own_sentiment": round(own[ticker], 3),
            "contagion": round(contagion, 3),
            "contagion_from": shocked_peers,
            "market_effect": round(market_effect, 3),
            "effective_sentiment": round(effective, 3),
            "n_signals": len(drivers[ticker]),
            "drivers": [
                {"text": s.snippet, "sentiment": s.sentiment, "impact": s.impact,
                 "event_type": s.event_type, "provider": s.provider}
                for _, s in top
            ],
        }

    target = _bound_and_normalise(raw, base)
    weights, turnover = _apply_turnover_cap(target, prev)
    for ticker in tickers:
        rows[ticker].update(
            base_weight=round(base, 4),
            weight=round(weights[ticker], 4),
            delta=round(weights[ticker] - base, 4),
            target_weight=round(target[ticker], 4),
        )
    return {
        "as_of": now.isoformat(),
        "stress_index": round(stress_index, 3),
        "regime": regime_of(stress_index),
        "turnover": round(turnover, 4),
        "market_sentiment": round(market, 3),
        "weights_map": weights,
        "table": sorted(rows.values(), key=lambda r: r["weight"], reverse=True),
    }


def simulate(signals: list[Sig], max_points: int = 60) -> tuple[list[dict], dict]:
    """Event-driven replay: rebalance after every batch of signals, in timestamp order."""
    tickers = list(TICKER_ALIASES)
    base_map = {t: 1 / len(tickers) for t in tickers}
    if not signals:
        empty = {
            "as_of": None, "stress_index": 0.0, "regime": "NORMAL", "turnover": 0.0,
            "market_sentiment": 0.0, "weights_map": base_map, "table": [],
        }
        return [], empty

    signals = sorted(signals, key=lambda s: s.ts)
    timestamps = [s.ts for s in signals]
    batch = max(1, math.ceil(len(signals) / max_points))
    ends = list(range(batch, len(signals), batch)) + [len(signals)]
    prev, steps, detail = base_map, [], {}
    for end in ends:
        now = signals[end - 1].ts
        left = bisect_left(timestamps, now - WINDOW, 0, end)
        detail = snapshot(signals[left:end], now, prev)
        prev = detail["weights_map"]
        steps.append({
            "timestamp": detail["as_of"],
            "weights": {t: round(w, 4) for t, w in prev.items()},
            "stress_index": detail["stress_index"],
            "regime": detail["regime"],
        })
    return steps, detail


def current_snapshot(max_points: int = 60) -> dict:
    _, detail = simulate(load_signals(), max_points)
    return {k: v for k, v in detail.items() if k != "weights_map"} | {
        "weights": {t: round(w, 4) for t, w in detail["weights_map"].items()}
    }


def timeline(max_points: int = 60) -> dict:
    steps, _ = simulate(load_signals(), max_points)
    return {"tickers": list(TICKER_ALIASES), "points": steps}
