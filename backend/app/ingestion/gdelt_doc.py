import hashlib
import time
from datetime import datetime, timezone
from typing import Iterator

import httpx

from app.ingestion.base import BaseSource
from app.ingestion.cache import get_json_cached
from app.schemas import RawDocument, SourceType

GDELT_DOC_URL = "https://api.gdeltproject.org/api/v2/doc/doc"


class GdeltDocSource(BaseSource):
    """GDELT DOC 2.0 article list. Returns headlines only (no article body)."""

    name = "gdelt_doc"

    def __init__(
        self,
        queries: list[str],
        timespan: str = "1d",
        max_records: int = 100,
        delay_seconds: float = 5.0,
    ):
        self.queries = queries
        self.timespan = timespan
        self.max_records = max_records
        self.delay_seconds = delay_seconds

    def fetch(self) -> Iterator[RawDocument]:
        with httpx.Client(timeout=30) as client:
            for query in self.queries:
                payload, from_network = get_json_cached(
                    client,
                    GDELT_DOC_URL,
                    params={
                        "query": f'"{query}" sourcelang:english',
                        "mode": "artlist",
                        "format": "json",
                        "timespan": self.timespan,
                        "maxrecords": self.max_records,
                        "sort": "datedesc",
                    },
                    cache_key=f"gdelt:{query}:{self.timespan}",
                )
                if from_network:
                    time.sleep(self.delay_seconds)  # stay polite with the API
                if not payload:
                    continue
                for article in payload.get("articles", []):
                    title = (article.get("title") or "").strip()
                    url = article.get("url") or ""
                    seen_date = article.get("seendate")
                    if not title or not url or not seen_date:
                        continue
                    try:
                        published_at = datetime.strptime(
                            seen_date, "%Y%m%dT%H%M%SZ"
                        ).replace(tzinfo=timezone.utc)
                    except ValueError:
                        continue
                    yield RawDocument(
                        doc_id=hashlib.sha1(url.encode()).hexdigest(),
                        source=SourceType.NEWS,
                        provider="gdelt",
                        published_at=published_at,
                        text=title,
                        url=url,
                        author=article.get("domain"),
                        meta={"query": query, "country": article.get("sourcecountry")},
                    )
