import json
import sqlite3

from app.config import DB_PATH
from app.schemas import RawDocument


def get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    connection.execute(
        """
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
        )
        """
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_documents_time ON documents(published_at)"
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_documents_scored ON documents(scored)"
    )
    return connection


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


def _row_to_dict(row: sqlite3.Row) -> dict:
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
        return [_row_to_dict(row) for row in connection.execute(query, params).fetchall()]
    finally:
        connection.close()


def get_stats() -> dict:
    connection = get_connection()
    try:
        total = connection.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
        by_provider = {
            row["provider"]: row["count"]
            for row in connection.execute(
                "SELECT provider, COUNT(*) AS count FROM documents GROUP BY provider"
            )
        }
        unscored = connection.execute(
            "SELECT COUNT(*) FROM documents WHERE scored = 0"
        ).fetchone()[0]
        no_entity = connection.execute(
            "SELECT COUNT(*) FROM documents WHERE tickers = '[]'"
        ).fetchone()[0]
        return {
            "total": total,
            "by_provider": by_provider,
            "unscored": unscored,
            "without_ticker": no_entity,
        }
    finally:
        connection.close()
