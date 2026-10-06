import hashlib
import xml.etree.ElementTree as ET
from datetime import timezone
from email.utils import parsedate_to_datetime
from typing import Iterator
from urllib.parse import quote_plus

import httpx

from app.ingestion.base import BaseSource
from app.ingestion.cache import get_json_cached
from app.schemas import RawDocument, SourceType

GOOGLE_NEWS_RSS = "https://news.google.com/rss/search"


class GoogleNewsRssSource(BaseSource):
    """Headlines from Google News RSS. No API key or account needed."""

    name = "google_news"

    def __init__(self, queries: list[str], recency: str = "1d"):
        self.queries = queries  # full search strings, e.g. "apple stock"
        self.recency = recency

    def fetch(self) -> Iterator[RawDocument]:
        headers = {"User-Agent": "Mozilla/5.0 (risk-engine hackathon)"}
        with httpx.Client(timeout=20, headers=headers, follow_redirects=True) as client:
            for query in self.queries:
                full_query = f"{query} when:{self.recency}"
                xml_text, _ = get_json_cached(
                    client,
                    GOOGLE_NEWS_RSS,
                    params={"q": full_query, "hl": "en-US", "gl": "US", "ceid": "US:en"},
                    cache_key=f"gnews:{full_query}",
                    as_text=True,
                )
                if not xml_text:
                    continue
                try:
                    root = ET.fromstring(xml_text)
                except ET.ParseError:
                    continue
                for item in root.iter("item"):
                    title = (item.findtext("title") or "").strip()
                    link = item.findtext("link") or ""
                    published_raw = item.findtext("pubDate")
                    if not title or not published_raw:
                        continue
                    try:
                        published_at = parsedate_to_datetime(published_raw)
                    except (TypeError, ValueError):
                        continue
                    if published_at.tzinfo is None:
                        published_at = published_at.replace(tzinfo=timezone.utc)

                    publisher = (item.findtext("source") or "").strip() or None
                    headline = title
                    if " - " in title:  # Google appends " - Publisher"
                        headline, _, tail = title.rpartition(" - ")
                        publisher = publisher or tail.strip()
                    yield RawDocument(
                        doc_id=hashlib.sha1((link or title).encode()).hexdigest(),
                        source=SourceType.NEWS,
                        provider="google_news",
                        published_at=published_at,
                        text=headline.strip(),
                        url=link or None,
                        author=publisher,
                        meta={"query": query},
                    )
