import json
import sqlite3

from app.config import DB_PATH
from app.schemas import RawDocument

SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    doc_id TEXT PRIMARY KEY,
    text_hash TEXT NOT NULL UNIQUE,
    source TEXT NOT NULL,
    provider TEXT NOT NULL,
    published_at TEXT NOT NULL,
    text TEXT NOT NULL,
    url TEXT,
    author TEXT,
    tickers TEXT NOT NULL,
    meta TEXT,
    scored INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_documents_time ON documents(published_at);
CREATE INDEX IF NOT EXISTS idx_documents_scored ON documents(scored);

CREATE TABLE IF NOT EXISTS signals (
    signal_id INTEGER PRIMARY KEY AUTOINCREMENT,
    doc_id TEXT NOT NULL,
    entity TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    source TEXT NOT NULL,
    provider TEXT NOT NULL,
    sentiment REAL NOT NULL,
    event_type TEXT NOT NULL,
    event_confidence REAL NOT NULL,
    impact INTEGER NOT NULL,
    confidence REAL NOT NULL,
    credibility REAL NOT NULL,
    text_snippet TEXT NOT NULL,
    url TEXT,
    breakdown TEXT,
    backend TEXT,
    UNIQUE(doc_id, entity)
);
CREATE INDEX IF NOT EXISTS idx_signals_time ON signals(timestamp);
CREATE INDEX IF NOT EXISTS idx_signals_entity ON signals(entity, event_type);
"""


def get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    connection.executescript(SCHEMA)
    return connection


# ----------------------------------------------------------------- documents
def insert_document(
    connection: sqlite3.Connection,
    document: RawDocument,
    text_hash: str,
    tickers: list[str],
) -> bool:
    """Return True if inserted, False if it was a duplicate (doc_id or text_hash)."""
    cursor = connection.execute(
        "INSERT OR IGNORE INTO documents "
        "(doc_id, text_hash, source, provider, published_at, text, url, author, tickers, meta) "
        "VALUES (?,?,?,?,?,?,?,?,?,?)",
        (
            document.doc_id,
            text_hash,
            document.source.value,
            document.provider,
            document.published_at.isoformat(),
            document.text,
            document.url,
            document.author,
            json.dumps(tickers),
            json.dumps(document.meta, default=str),
        ),
    )
    connection.commit()
    return cursor.rowcount == 1


def _document_to_dict(row: sqlite3.Row) -> dict:
    item = dict(row)
    item["tickers"] = json.loads(item["tickers"])
    item["meta"] = json.loads(item["meta"] or "{}")
    item["scored"] = bool(item["scored"])
    return item


def list_documents(
    ticker: str | None = None,
    source: str | None = None,
    provider: str | None = None,
    since: str | None = None,
    unscored_only: bool = False,
    limit: int = 50,
) -> list[dict]:
    clauses, params = [], []
    if ticker:
        clauses.append("tickers LIKE ?")
        params.append(f'%"{ticker.upper()}"%')
    if source:
        clauses.append("source = ?")
        params.append(source)
    if provider:
        clauses.append("provider = ?")
        params.append(provider)
    if since:
        clauses.append("published_at >= ?")
        params.append(since)
    if unscored_only:
        clauses.append("scored = 0")
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    query = f"SELECT * FROM documents {where} ORDER BY published_at DESC LIMIT ?"
    params.append(limit)
    connection = get_connection()
    try:
        return [_document_to_dict(row) for row in connection.execute(query, params).fetchall()]
    finally:
        connection.close()


def fetch_unscored(connection: sqlite3.Connection, limit: int) -> list[dict]:
    rows = connection.execute(
        "SELECT * FROM documents WHERE scored = 0 ORDER BY published_at LIMIT ?", (limit,)
    ).fetchall()
    return [_document_to_dict(row) for row in rows]


def mark_scored(connection: sqlite3.Connection, doc_ids: list[str]) -> None:
    connection.executemany(
        "UPDATE documents SET scored = 1 WHERE doc_id = ?", [(doc_id,) for doc_id in doc_ids]
    )
    connection.commit()


# ------------------------------------------------------------------- signals
def insert_signal(connection: sqlite3.Connection, signal: dict) -> bool:
    cursor = connection.execute(
        "INSERT OR IGNORE INTO signals "
        "(doc_id, entity, timestamp, source, provider, sentiment, event_type, event_confidence, "
        "impact, confidence, credibility, text_snippet, url, breakdown, backend) "
        "VALUES (:doc_id,:entity,:timestamp,:source,:provider,:sentiment,:event_type,"
        ":event_confidence,:impact,:confidence,:credibility,:text_snippet,:url,:breakdown,:backend)",
        {**signal, "breakdown": json.dumps(signal.get("breakdown", {}))},
    )
    return cursor.rowcount == 1


def count_corroboration(connection, entity: str, event_type: str, start: str, end: str) -> int:
    row = connection.execute(
        "SELECT COUNT(*) FROM signals WHERE entity = ? AND event_type = ? "
        "AND timestamp BETWEEN ? AND ?",
        (entity, event_type, start, end),
    ).fetchone()
    return int(row[0])


def _signal_to_dict(row: sqlite3.Row) -> dict:
    item = dict(row)
    item["breakdown"] = json.loads(item["breakdown"] or "{}")
    return item


def list_signals(
    ticker: str | None = None,
    event_type: str | None = None,
    min_impact: int = 1,
    provider: str | None = None,
    since: str | None = None,
    limit: int = 100,
    newest_first: bool = True,
) -> list[dict]:
    clauses, params = ["impact >= ?"], [min_impact]
    if ticker:
        clauses.append("entity = ?")
        params.append(ticker.upper())
    if event_type:
        clauses.append("event_type = ?")
        params.append(event_type)
    if provider:
        clauses.append("provider = ?")
        params.append(provider)
    if since:
        clauses.append("timestamp >= ?")
        params.append(since)
    order = "DESC" if newest_first else "ASC"
    query = (
        f"SELECT * FROM signals WHERE {' AND '.join(clauses)} "
        f"ORDER BY timestamp {order} LIMIT ?"
    )
    params.append(limit)
    connection = get_connection()
    try:
        return [_signal_to_dict(row) for row in connection.execute(query, params).fetchall()]
    finally:
        connection.close()


def latest_signal_time() -> str | None:
    connection = get_connection()
    try:
        row = connection.execute("SELECT MAX(timestamp) FROM signals").fetchone()
        return row[0]
    finally:
        connection.close()


def delete_provider(provider: str) -> dict:
    connection = get_connection()
    try:
        signals = connection.execute("DELETE FROM signals WHERE provider = ?", (provider,)).rowcount
        documents = connection.execute(
            "DELETE FROM documents WHERE provider = ?", (provider,)
        ).rowcount
        connection.commit()
        return {"signals_deleted": signals, "documents_deleted": documents}
    finally:
        connection.close()


# --------------------------------------------------------------------- stats
def get_stats() -> dict:
    connection = get_connection()
    try:
        scalar = lambda query: connection.execute(query).fetchone()[0]  # noqa: E731
        by_provider = {
            row["provider"]: row["count"]
            for row in connection.execute(
                "SELECT provider, COUNT(*) AS count FROM documents GROUP BY provider"
            )
        }
        by_event = {
            row["event_type"]: row["count"]
            for row in connection.execute(
                "SELECT event_type, COUNT(*) AS count FROM signals GROUP BY event_type "
                "ORDER BY count DESC"
            )
        }
        return {
            "total": scalar("SELECT COUNT(*) FROM documents"),
            "by_provider": by_provider,
            "unscored": scalar("SELECT COUNT(*) FROM documents WHERE scored = 0"),
            "without_ticker": scalar("SELECT COUNT(*) FROM documents WHERE tickers = '[]'"),
            "signals": scalar("SELECT COUNT(*) FROM signals"),
            "signals_by_event": by_event,
        }
    finally:
        connection.close()
