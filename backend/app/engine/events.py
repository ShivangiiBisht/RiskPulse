"""Event classification into a fixed taxonomy + base market-impact severity per event type."""
import logging
import re
from functools import lru_cache

from app.config import EVENT_BACKEND

log = logging.getLogger("risk_engine.events")

# Order matters: ties are resolved in favour of the more severe event type listed first.
RULES: dict[str, list[tuple[str, float]]] = {
    "Credit Event": [
        (r"\bdefaults?\b", 1.5), (r"\bbankrupt(cy)?\b", 1.5), (r"\binsolven\w*", 1.5),
        (r"\bdowngrad\w*", 1.0), (r"\bbail-?outs?\b", 1.5), (r"\bbank runs?\b", 1.5),
        (r"\bcredit (rating|losses|crunch)\b", 1.0), (r"\bloan losses\b", 1.0),
        (r"\bhalts? withdrawals\b", 1.5), (r"\bwrite-?downs?\b", 1.0), (r"\bdistress\w*", 1.0),
        (r"\bliquidity\b", 0.8), (r"\bcreditors?\b", 0.8), (r"\bcollapse[sd]?\b", 0.8),
    ],
    "Geopolitical": [
        (r"\bwar\b", 1.5), (r"\binvasion\b|\binvad\w+", 1.5), (r"\bsanctions?\b", 1.5),
        (r"\bmissiles?\b", 1.0), (r"\bmilitary\b", 1.0), (r"\bceasefire\b", 1.0),
        (r"\btensions?\b", 0.8), (r"\bconflicts?\b", 1.0), (r"\bgeopolitic\w*", 1.5),
        (r"\bembargo\b", 1.5), (r"\bnato\b", 1.0), (r"\bterror\w*", 1.0), (r"\bcoup\b", 1.0),
        (r"\btariffs?\b", 1.0), (r"\bstrikes? (on|against)\b", 0.8),
    ],
    "Macroeconomic": [
        (r"\binflation\b", 1.0), (r"\bcpi\b", 1.0), (r"\binterest rates?\b", 1.5),
        (r"\brate (hikes?|cuts?)\b", 1.5), (r"\bfed(eral reserve)?\b", 1.0), (r"\becb\b", 1.0),
        (r"\bgdp\b", 1.0), (r"\brecession\b", 1.5), (r"\bunemployment\b", 1.0),
        (r"\bjobs? (report|data)\b", 1.0), (r"\bcentral banks?\b", 1.0),
        (r"\btreasury yields?\b|\byields? (jump|surge|fall)\w*", 1.0), (r"\boil prices?\b", 1.0),
        (r"\bopec\b", 1.0), (r"\bstimulus\b", 1.0), (r"\bpayrolls?\b", 1.0),
    ],
    "Regulatory": [
        (r"\bsec\b", 1.0), (r"\bantitrust\b", 1.5), (r"\bregulators?\b", 1.0),
        (r"\bfined?\b", 1.0), (r"\bprobe\b|\binvestigat\w+", 1.0), (r"\blawsuits?\b|\bsues?\b|\bsued\b", 1.0),
        (r"\bsettlement\b", 1.0), (r"\bbans?\b|\bbanned\b", 1.0), (r"\bcompliance\b", 1.0),
        (r"\bdoj\b|\bftc\b", 1.0), (r"\beu commission\b", 1.0), (r"\bsubpoena\w*", 1.0),
        (r"\bapproval\b|\bapproves?\b", 0.6),
    ],
    "Merger/Acquisition": [
        (r"\bacqui\w+", 1.5), (r"\bmerger\b|\bmerges?\b|\bmerging\b", 1.5), (r"\btakeover\b", 1.5),
        (r"\bbuy-?out\b", 1.5), (r"\bbids? for\b", 1.0), (r"\bdeal to (buy|acquire)\b", 1.5),
        (r"\bdivest\w*", 1.0), (r"\bspin-?off\b", 1.0),
    ],
    "Earnings": [
        (r"\bearnings\b", 1.5), (r"\beps\b", 1.0), (r"\brevenues?\b", 1.0), (r"\bprofits?\b", 0.8),
        (r"\bquarterly (results|report)\b|\bquarter\b", 1.0), (r"\bguidance\b", 1.0),
        (r"\b(beats?|misses?) (earnings )?estimates\b", 1.5), (r"\boutlook\b|\bforecast\b", 0.8),
        (r"\bdividend\b|\bbuy-?back\b", 0.8),
    ],
    "Product Launch": [
        (r"\blaunch\w*", 1.5), (r"\bunveil\w*", 1.5), (r"\breleases?\b|\breleased\b", 1.0),
        (r"\bdebuts?\b", 1.0), (r"\brolls? out\b|\brollout\b", 1.0), (r"\bnew (product|iphone|model|lineup)\b", 1.0),
        (r"\bintroduces?\b", 1.0),
    ],
}
EVENT_TYPES = [*RULES, "Other"]

# Base market-impact severity (0-10) per event type: a documented modelling assumption.
BASE_SEVERITY: dict[str, float] = {
    "Credit Event": 8.5, "Geopolitical": 7.5, "Macroeconomic": 6.5, "Regulatory": 6.0,
    "Merger/Acquisition": 5.5, "Earnings": 4.5, "Product Launch": 3.0, "Other": 2.0,
}

_COMPILED = {
    event: [(re.compile(pattern, re.IGNORECASE), weight) for pattern, weight in patterns]
    for event, patterns in RULES.items()
}


def _classify_rules(text: str) -> tuple[str, float]:
    scores = {
        event: sum(weight for pattern, weight in patterns if pattern.search(text))
        for event, patterns in _COMPILED.items()
    }
    total = sum(scores.values())
    if total == 0:
        return "Other", 0.3
    best = max(scores, key=scores.get)  # first maximum wins -> severity-ordered tie-break
    confidence = (scores[best] / (total + 0.5)) * min(1.0, 0.5 + 0.25 * scores[best])
    return best, round(min(0.95, confidence), 3)


@lru_cache(maxsize=1)
def _zero_shot_pipeline():
    from transformers import pipeline

    return pipeline("zero-shot-classification", model="facebook/bart-large-mnli")


def classify_event(text: str) -> tuple[str, float, str]:
    """Return (event_type, confidence, backend)."""
    if EVENT_BACKEND == "zeroshot":
        try:
            result = _zero_shot_pipeline()(text, list(RULES))
            return result["labels"][0], round(float(result["scores"][0]), 3), "zeroshot"
        except Exception as error:  # noqa: BLE001
            log.warning("Zero-shot classifier unavailable (%r); using rules", error)
    event, confidence = _classify_rules(text)
    return event, confidence, "rules"
