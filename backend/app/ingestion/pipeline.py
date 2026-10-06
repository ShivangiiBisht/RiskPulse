import hashlib
import html
import re

from app.db import get_connection, insert_document
from app.entities import extract_tickers, normalize_ticker
from app.ingestion.base import BaseSource

_URL = re.compile(r"https?://\S+")
_RETWEET = re.compile(r"^rt\s+@\w+:\s*", re.IGNORECASE)
_SPACES = re.compile(r"\s+")
_SOURCE_SUFFIX = re.compile(r"\s[-|\u2013\u2014]\s[^-|\u2013\u2014]{2,40}$")  # " - Reuters"
_NON_ALNUM = re.compile(r"[^a-z0-9]+")


def clean_text(text: str) -> str:
    text = html.unescape(text)
    text = _RETWEET.sub("", text)
    text = _URL.sub("", text)
    return _SPACES.sub(" ", text).strip()


def normalize_for_hash(text: str) -> str:
    """Collapse trivial variations so syndicated copies hash identically."""
    text = _SOURCE_SUFFIX.sub("", text.lower())
    return _NON_ALNUM.sub(" ", text).strip()


def run_ingestion(source: BaseSource, min_length: int = 15) -> dict:
    stats = {
        "source": source.name,
        "seen": 0,
        "inserted": 0,
        "duplicates": 0,
        "too_short": 0,
        "without_ticker": 0,
    }
    connection = get_connection()
    try:
        for document in source.fetch():
            stats["seen"] += 1
            document.text = clean_text(document.text)
            if len(document.text) < min_length:
                stats["too_short"] += 1
                continue

            tickers = set(extract_tickers(document.text))
            dataset_ticker = normalize_ticker(document.meta.get("dataset_ticker"))
            if dataset_ticker:
                tickers.add(dataset_ticker)
            if not tickers:
                # Still stored: macro/geopolitical events matter for Module B.
                stats["without_ticker"] += 1

            text_hash = hashlib.sha1(normalize_for_hash(document.text).encode()).hexdigest()
            if insert_document(connection, document, text_hash, sorted(tickers)):
                stats["inserted"] += 1
            else:
                stats["duplicates"] += 1
    finally:
        connection.close()
    return stats
