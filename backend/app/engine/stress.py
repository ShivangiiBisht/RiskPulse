"""Module B - event-driven portfolio stress test on a synthetic wholesale-banking book.

A high-impact event (default: impact >= 7) selects a shock row by event type (data/shocks.json).
Shocks are scaled by impact/8 and amplified 1.5x for assets linked to the tickers named in the event.
Revaluation (deliberately simple, documented in the README):
  equity       dV = V * equity_shock * beta
  bond         dV/V = -D*(dy+ds) + 0.5*C*(dy+ds)^2      (ds = spread shock * rating multiplier)
  loan         loss = notional * LGD * (PD_stressed - PD), PD_stressed = PD * (1 + 0.5 * spread_shock_pct)
  equity swap  dV = notional * delta * equity_shock * beta
  IR swap      dV = notional * duration * dy * direction (+1 pay-fixed, -1 receive-fixed)
"""
import csv
import json
from datetime import datetime, timedelta
from functools import lru_cache

from app.config import INPUT_DIR
from app.db import list_signals, latest_signal_time
from app.entities import beta_of

RATING_SPREAD_MULT = {"AAA": 0.2, "AA": 0.4, "A": 0.7, "BBB": 1.0, "BB": 1.8, "B": 2.5}
IDIOSYNCRATIC_MULT = 1.5
TRIGGER_IMPACT = 7


@lru_cache(maxsize=1)
def load_shocks() -> dict:
    return json.loads((INPUT_DIR / "shocks.json").read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def load_portfolio() -> list[dict]:
    with open(INPUT_DIR / "portfolio.csv", newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    numeric = ("notional_musd", "market_value_musd", "duration", "convexity", "pd", "lgd", "delta", "direction")
    for row in rows:
        for key in numeric:
            row[key] = float(row[key]) if row.get(key) not in (None, "") else 0.0
    return rows


def _asset_pnl(asset: dict, shock: dict, scale: float, affected: set[str]) -> float:
    idio = IDIOSYNCRATIC_MULT if asset["ticker"] in affected else 1.0
    equity = shock["equity_shock"] * scale
    dy = shock["rate_shift_bp"] * scale / 1e4
    spread_bp = shock["spread_shift_bp"] * scale * idio
    mult = RATING_SPREAD_MULT.get(asset["rating"], 1.0)
    beta = beta_of(asset["ticker"])
    kind = asset["asset_type"]

    if kind == "equity":
        return asset["market_value_musd"] * equity * beta * idio
    if kind == "bond":
        total = dy + spread_bp * mult / 1e4
        pct = -asset["duration"] * total + 0.5 * asset["convexity"] * total**2
        return asset["market_value_musd"] * pct
    if kind == "loan":
        pd_stressed = min(1.0, asset["pd"] * (1 + 0.5 * spread_bp * mult / 100))
        return -asset["notional_musd"] * asset["lgd"] * (pd_stressed - asset["pd"])
    if kind == "derivative" and asset["subtype"] == "equity_swap":
        return asset["notional_musd"] * asset["delta"] * equity * beta * idio
    if kind == "derivative":  # ir_swap
        return asset["notional_musd"] * asset["duration"] * dy * asset["direction"]
    return 0.0


def run_stress(
    event_type: str, impact: int, tickers: list[str] | None = None, headline: str | None = None
) -> dict:
    shocks = load_shocks()
    shock = shocks.get(event_type, shocks["Other"])
    scale = max(0.25, impact / 8)
    affected = set(tickers or [])
    portfolio = load_portfolio()

    classes: dict[str, dict] = {}
    losers = []
    for asset in portfolio:
        pnl = _asset_pnl(asset, shock, scale, affected)
        bucket = classes.setdefault(asset["asset_type"], {"before": 0.0, "pnl": 0.0, "exposure": 0.0})
        bucket["before"] += asset["market_value_musd"]
        # derivatives carry ~zero market value, so express their P&L against gross notional
        bucket["exposure"] += asset["notional_musd"] if asset["asset_type"] == "derivative" else asset["market_value_musd"]
        bucket["pnl"] += pnl
        losers.append({
            "asset_id": asset["asset_id"], "asset_type": asset["asset_type"],
            "counterparty": asset["counterparty"], "ticker": asset["ticker"],
            "pnl": round(pnl, 3), "linked_to_event": asset["ticker"] in affected,
        })

    by_class = [
        {
            "asset_class": name,
            "before": round(v["before"], 2),
            "pnl": round(v["pnl"], 2),
            "after": round(v["before"] + v["pnl"], 2),
            "pnl_pct": round(100 * v["pnl"] / v["exposure"], 2) if v["exposure"] else 0.0,
            "exposure": round(v["exposure"], 2),
        }
        for name, v in classes.items()
    ]
    before = sum(c["before"] for c in by_class)
    pnl_total = sum(c["pnl"] for c in by_class)
    return {
        "event_type": event_type,
        "impact": impact,
        "scale": round(scale, 3),
        "tickers": sorted(affected),
        "headline": headline,
        "shocks": shock,
        "before": round(before, 2),
        "after": round(before + pnl_total, 2),
        "pnl": round(pnl_total, 2),
        "pnl_pct": round(100 * pnl_total / before, 2) if before else 0.0,
        "by_asset_class": by_class,
        "top_losers": sorted(losers, key=lambda row: row["pnl"])[:10],
        "assets": len(portfolio),
    }


def auto_trigger(threshold: int = TRIGGER_IMPACT, window_hours: int = 48) -> dict:
    """Find the dominant high-impact event among recent signals and stress the book with it."""
    latest = latest_signal_time()
    if latest is None:
        return {"triggered": False, "reason": "No signals yet. Ingest and score data first."}
    since = (datetime.fromisoformat(latest) - timedelta(hours=window_hours)).isoformat()
    recent = list_signals(min_impact=threshold, since=since, limit=500)
    if not recent:
        return {"triggered": False, "reason": f"No event with impact >= {threshold} in the last {window_hours}h."}

    groups: dict[str, list[dict]] = {}
    for signal in recent:
        groups.setdefault(signal["event_type"], []).append(signal)
    event_type, members = max(
        groups.items(), key=lambda item: (max(s["impact"] for s in item[1]), len(item[1]))
    )
    lead = max(members, key=lambda s: (s["impact"], s["timestamp"]))
    tickers = sorted({s["entity"] for s in members if s["entity"] != "MARKET"})
    result = run_stress(event_type, lead["impact"], tickers, lead["text_snippet"])
    result["supporting_signals"] = len(members)
    return {"triggered": True, "threshold": threshold, "result": result}
