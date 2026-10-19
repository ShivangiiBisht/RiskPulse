"""Turns unscored documents into structured risk signals.

Signal = {entity, sentiment [-1,1], event_type, impact [1,10], confidence, evidence + score breakdown}.
Impact is an explainable composite (no labelled data exists), not a black box:

    impact = clamp(round(1 + 9 * severity * magnitude * credibility * corroboration), 1, 10)
      severity      = base severity of the event type / 10
      magnitude     = 0.5 + 0.5 * |sentiment|           (strong language -> larger move)
      credibility   = publisher / channel reliability   (tweets count less than wire services)
      corroboration = 1 + 0.15 * log2(#same-event signals for this entity in +-24h), capped at 1.5
"""
import math
from datetime import datetime, timedelta

from app.db import (
    count_corroboration,
    fetch_unscored,
    get_connection,
    insert_signal,
    mark_scored,
)
from app.engine.events import BASE_SEVERITY, classify_event
from app.engine.sentiment import score_sentiment

MARKET = "MARKET"  # entity used for macro / geopolitical items that name no tracked company

CREDIBILITY_BY_PUBLISHER = {
    "reuters": 1.0, "bloomberg": 1.0, "wsj": 1.0, "wall street journal": 1.0,
    "financial times": 1.0, "ft.com": 1.0, "cnbc": 0.95, "associated press": 0.95,
    "marketwatch": 0.9, "barron": 0.9, "yahoo": 0.85, "investopedia": 0.8,
    "seeking alpha": 0.7, "motley fool": 0.7,
}


def source_credibility(provider: str, author: str | None) -> float:
    if provider == "tweet_replay":
        return 0.5
    if provider == "sandbox":
        return 0.9
    name = (author or "").lower()
    for key, value in CREDIBILITY_BY_PUBLISHER.items():
        if key in name:
            return value
    return 0.75


def compute_impact(
    event_type: str, sentiment: float, credibility: float, corroboration: int
) -> tuple[int, dict]:
    severity = BASE_SEVERITY[event_type] / 10
    magnitude = 0.5 + 0.5 * abs(sentiment)
    boost = min(1.5, 1 + 0.15 * math.log2(max(1, corroboration)))
    raw = severity * magnitude * credibility * boost
    impact = max(1, min(10, round(1 + 9 * raw)))
    return impact, {
        "severity": round(severity, 3),
        "magnitude": round(magnitude, 3),
        "credibility": round(credibility, 3),
        "corroboration": corroboration,
        "corroboration_boost": round(boost, 3),
        "raw": round(raw, 3),
    }


def score_pending(max_documents: int = 5000, batch_size: int = 64) -> dict:
    stats = {"documents": 0, "signals": 0, "sentiment_backend": None, "event_backend": None}
    connection = get_connection()
    try:
        while stats["documents"] < max_documents:
            rows = fetch_unscored(connection, batch_size)
            if not rows:
                break
            sentiments, stats["sentiment_backend"] = score_sentiment([r["text"] for r in rows])
            for row, (sentiment, sentiment_confidence) in zip(rows, sentiments):
                event_type, event_confidence, stats["event_backend"] = classify_event(row["text"])
                credibility = source_credibility(row["provider"], row["author"])
                published = datetime.fromisoformat(row["published_at"])
                window = (
                    (published - timedelta(hours=24)).isoformat(),
                    (published + timedelta(hours=24)).isoformat(),
                )
                for entity in row["tickers"] or [MARKET]:
                    corroboration = 1 + count_corroboration(
                        connection, entity, event_type, *window
                    )
                    impact, breakdown = compute_impact(
                        event_type, sentiment, credibility, corroboration
                    )
                    inserted = insert_signal(connection, {
                        "doc_id": row["doc_id"],
                        "entity": entity,
                        "timestamp": row["published_at"],
                        "source": row["source"],
                        "provider": row["provider"],
                        "sentiment": sentiment,
                        "event_type": event_type,
                        "event_confidence": event_confidence,
                        "impact": impact,
                        "confidence": round(0.6 * sentiment_confidence + 0.4 * event_confidence, 3),
                        "credibility": credibility,
                        "text_snippet": row["text"][:240],
                        "url": row["url"],
                        "breakdown": breakdown,
                        "backend": f"{stats['sentiment_backend']}+{stats['event_backend']}",
                    })
                    stats["signals"] += int(inserted)
            connection.commit()
            mark_scored(connection, [row["doc_id"] for row in rows])
            stats["documents"] += len(rows)
    finally:
        connection.close()
    return stats
