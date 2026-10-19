"""What-if sandbox: inject synthetic headlines / crisis scenarios and watch the engine react live.

Sandbox documents use provider="sandbox", bypass text de-duplication (so a demo can be repeated) and are
removed again with reset(), leaving real ingested data untouched.
"""
import hashlib
import json
import uuid
from datetime import datetime, timedelta, timezone

from app.config import INPUT_DIR
from app.db import delete_provider, get_connection, insert_document, list_signals
from app.engine import rebalancer
from app.engine.scoring import score_pending
from app.engine.stress import TRIGGER_IMPACT, run_stress
from app.entities import extract_tickers
from app.ingestion.pipeline import clean_text
from app.schemas import RawDocument, SourceType


def load_scenarios() -> list[dict]:
    return json.loads((INPUT_DIR / "scenarios.json").read_text(encoding="utf-8"))


def _inject(headlines: list[tuple[str, int]]) -> list[str]:
    """Insert + score headlines (text, minute_offset). Returns the inserted doc ids."""
    now = datetime.now(timezone.utc).replace(microsecond=0)
    connection = get_connection()
    doc_ids = []
    try:
        for text, minutes in headlines:
            text = clean_text(text)
            nonce = uuid.uuid4().hex
            doc_id = hashlib.sha1(f"sandbox{nonce}".encode()).hexdigest()
            document = RawDocument(
                doc_id=doc_id, source=SourceType.NEWS, provider="sandbox",
                published_at=now + timedelta(minutes=minutes), text=text, author="Sandbox",
            )
            insert_document(connection, document, hashlib.sha1(nonce.encode()).hexdigest(),
                            extract_tickers(text))
            doc_ids.append(doc_id)
    finally:
        connection.close()
    score_pending()
    return doc_ids


def _report(before: dict, doc_ids: list[str]) -> dict:
    after = rebalancer.current_snapshot()
    new_signals = [s for s in list_signals(provider="sandbox", limit=500, newest_first=False)
                   if s["doc_id"] in set(doc_ids)]
    changes = sorted(
        (
            {"ticker": t, "before": before["weights"][t], "after": after["weights"][t],
             "delta": round(after["weights"][t] - before["weights"][t], 4)}
            for t in after["weights"]
        ),
        key=lambda row: abs(row["delta"]), reverse=True,
    )[:8]

    stress = None
    severe = [s for s in new_signals if s["impact"] >= TRIGGER_IMPACT]
    if severe:
        lead = max(severe, key=lambda s: s["impact"])
        tickers = sorted({s["entity"] for s in severe if s["entity"] != "MARKET"})
        stress = run_stress(lead["event_type"], lead["impact"], tickers, lead["text_snippet"])

    return {
        "signals": new_signals,
        "regime_before": before["regime"], "regime_after": after["regime"],
        "stress_index_before": before["stress_index"], "stress_index_after": after["stress_index"],
        "weight_changes": changes,
        "stress_test": stress,
    }


def inject_headline(text: str) -> dict:
    before = rebalancer.current_snapshot()
    return _report(before, _inject([(text, 0)]))


def run_scenario(scenario_id: str) -> dict | None:
    scenario = next((s for s in load_scenarios() if s["id"] == scenario_id), None)
    if scenario is None:
        return None
    before = rebalancer.current_snapshot()
    report = _report(before, _inject([(h["text"], h["minutes"]) for h in scenario["headlines"]]))
    report["scenario"] = {"id": scenario["id"], "name": scenario["name"]}
    return report


def reset() -> dict:
    return delete_provider("sandbox")
