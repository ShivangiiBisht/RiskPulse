from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class SourceType(str, Enum):
    NEWS = "news"
    TWITTER = "twitter"


class RawDocument(BaseModel):
    doc_id: str
    source: SourceType
    provider: str  # newsapi | gdelt | tweet_replay
    published_at: datetime
    text: str
    url: str | None = None
    author: str | None = None
    meta: dict = Field(default_factory=dict)
