import hashlib
from datetime import datetime, timedelta, timezone
from typing import Iterator

import httpx

from app.config import FINNHUB_API_KEY, OFFLINE_MODE
from app.entities import TICKER_ALIASES
from app.ingestion.base import BaseSource
from app.ingestion.cache import get_json_cached
from app.schemas import RawDocument, SourceType

FINNHUB_URL = "https://finnhub.io/api/v1/company-news"


class FinnhubNewsSource(BaseSource):
    """Per-ticker company news from Finnhub (free API key, any email)."""

    name = "finnhub"

    def __init__(self, tickers: list[str] | None = None, lookback_days: int = 3):
        if not FINNHUB_API_KEY and not OFFLINE_MODE:
            raise RuntimeError("FINNHUB_API_KEY is not set (or enable OFFLINE_MODE=1)")
        self.tickers = tickers or list(TICKER_ALIASES)
        self.lookback_days = lookback_days

    def fetch(self) -> Iterator[RawDocument]:
        today = datetime.now(timezone.utc).date()
        start = today - timedelta(days=self.lookback_days)
        with httpx.Client(timeout=20) as client:
            for ticker in self.tickers:
                payload, _ = get_json_cached(
                    client,
                    FINNHUB_URL,
                    params={
                        "symbol": ticker,
                        "from": start.isoformat(),
                        "to": today.isoformat(),
                        "token": FINNHUB_API_KEY,
                    },
                    cache_key=f"finnhub:{ticker}:{self.lookback_days}",
                )
                if not isinstance(payload, list):
                    continue
                for article in payload:
                    headline = (article.get("headline") or "").strip()
                    summary = (article.get("summary") or "").strip()
                    timestamp = article.get("datetime")
                    if not headline or not timestamp:
                        continue
                    url = article.get("url") or ""
                    text = f"{headline}. {summary}" if summary else headline
                    yield RawDocument(
                        doc_id=hashlib.sha1((url or text).encode()).hexdigest(),
                        source=SourceType.NEWS,
                        provider="finnhub",
                        published_at=datetime.fromtimestamp(timestamp, tz=timezone.utc),
                        text=text,
                        url=url or None,
                        author=article.get("source"),
                        meta={"dataset_ticker": ticker},
                    )
