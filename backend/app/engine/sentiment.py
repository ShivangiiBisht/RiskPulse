"""Sentiment scoring in [-1, 1].

Backends
- finbert : ProsusAI/finbert, score = P(positive) - P(negative)   (needs `pip install -r requirements-ml.txt`)
- lexicon : finance word lists + negation handling, no downloads  (always available)
- auto    : FinBERT if transformers+torch are installed, otherwise lexicon.
Any FinBERT failure (no model, no network) falls back to the lexicon, so the pipeline never stops.
"""
import importlib.util
import logging
import math
import re
from functools import lru_cache

from app.config import SENTIMENT_BACKEND

log = logging.getLogger("risk_engine.sentiment")
_TOKEN = re.compile(r"[a-z']+")

_POSITIVE = (
    "beat beats surge surges surged soar soars soared rally rallies rallied jump jumps jumped "
    "gain gains gained rise rises rose record upgrade upgraded upgrades outperform strong "
    "stronger growth profit profits profitable boost boosts approval approved approves "
    "breakthrough expands expansion rebound rebounds recovery recover bullish optimism raised "
    "raises exceeds exceeded wins win won dividend buyback partnership innovative demand "
    "unveils launches"
).split()
_NEGATIVE = (
    "miss misses missed plunge plunges plunged tumble tumbles tumbled slump slumps slide slides "
    "crash crashes collapse collapses collapsed default defaults bankruptcy bankrupt insolvency "
    "fraud probe lawsuit sues sued fine fined penalty downgrade downgraded downgrades cut cuts "
    "layoffs weak weaker loss losses decline declines fall falls fell drop drops dropped "
    "warning warns warned risk risks recall investigation sanctions war invasion attack "
    "conflict crisis recession shortage bearish fears fear selloff lowered delays halt halts "
    "hack breach strike shutdown bailout writedown impairment contagion turmoil plummets "
    "hike hikes inflation tensions escalate escalates seize seized disappoints "
    "strikes missile missiles military withdrawals"
).split()
_MILD = {"risk", "risks", "inflation", "hike", "hikes", "tensions", "cut", "cuts", "fall", "falls",
         "fear", "fears", "warning", "warns", "rise", "rises", "demand"}
_STRONG = {"collapse", "collapses", "collapsed", "crash", "plunge", "plunges", "bankruptcy",
           "bankrupt", "default", "fraud", "surge", "surges", "soar", "soars", "record",
           "breakthrough", "crisis", "insolvency", "bailout"}
_NEGATORS = {"no", "not", "never", "without", "fails", "failed", "unlikely", "denies"}

POSITIVE = {word: 0.5 if word in _MILD else 1.0 for word in _POSITIVE}
NEGATIVE = {word: 0.5 if word in _MILD else 1.0 for word in _NEGATIVE}


def _lexicon_score(text: str) -> tuple[float, float]:
    tokens = _TOKEN.findall(text.lower())
    raw, hits = 0.0, 0
    for index, token in enumerate(tokens):
        polarity = POSITIVE.get(token, 0.0) - NEGATIVE.get(token, 0.0)
        if polarity == 0.0:
            continue
        if token in _STRONG:
            polarity *= 1.5
        if any(prev in _NEGATORS for prev in tokens[max(0, index - 3):index]):
            polarity = -polarity
        raw += polarity
        hits += 1
    score = math.tanh(0.8 * raw)
    confidence = 0.3 if hits == 0 else min(0.9, 0.45 + 0.15 * hits)
    return round(score, 4), round(confidence, 3)


_finbert_failed = False


@lru_cache(maxsize=1)
def _finbert_pipeline():
    from transformers import pipeline  # imported lazily: heavy dependency

    return pipeline("text-classification", model="ProsusAI/finbert", top_k=None, truncation=True)


def _finbert_enabled() -> bool:
    if SENTIMENT_BACKEND == "lexicon" or _finbert_failed:
        return False
    if SENTIMENT_BACKEND == "finbert":
        return True
    return all(importlib.util.find_spec(name) for name in ("transformers", "torch"))


def score_sentiment(texts: list[str]) -> tuple[list[tuple[float, float]], str]:
    """Return ([(score, confidence), ...], backend_name)."""
    global _finbert_failed
    if _finbert_enabled():
        try:
            outputs = _finbert_pipeline()(texts, batch_size=16)
            results = []
            for labels in outputs:
                probs = {item["label"].lower(): item["score"] for item in labels}
                score = probs.get("positive", 0.0) - probs.get("negative", 0.0)
                results.append((round(score, 4), round(max(probs.values()), 3)))
            return results, "finbert"
        except Exception as error:  # noqa: BLE001 - any failure falls back to the lexicon
            _finbert_failed = True
            log.warning("FinBERT unavailable (%r); falling back to lexicon scorer", error)
    return [_lexicon_score(text) for text in texts], "lexicon"
