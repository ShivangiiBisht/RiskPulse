import hashlib
import time
from pathlib import Path
from typing import Iterator

import pandas as pd

from app.ingestion.base import BaseSource
from app.schemas import RawDocument, SourceType


class TweetReplaySource(BaseSource):
    """
    Replays a Kaggle stock-tweets CSV in timestamp order.

    Column names are normalised (lowercase, spaces -> underscores), so
    "Stock Name" is referenced as "stock_name".
    speed = simulated seconds per real second (0 = no waiting, bulk load).
    """

    name = "tweet_replay"

    def __init__(
        self,
        csv_path: str | Path,
        text_col: str = "tweet",
        date_col: str = "date",
        ticker_col: str | None = "stock_name",
        speed: float = 0.0,
        limit: int | None = None,
    ):
        self.csv_path = Path(csv_path)
        self.text_col = text_col
        self.date_col = date_col
        self.ticker_col = ticker_col
        self.speed = speed
        self.limit = limit

    def fetch(self) -> Iterator[RawDocument]:
        if not self.csv_path.exists():
            raise FileNotFoundError(f"Tweet CSV not found: {self.csv_path}")

        frame = pd.read_csv(self.csv_path)
        frame.columns = [c.strip().lower().replace(" ", "_") for c in frame.columns]
        for required in (self.text_col, self.date_col):
            if required not in frame.columns:
                raise KeyError(
                    f"Column '{required}' not in CSV. Available: {list(frame.columns)}"
                )

        frame[self.date_col] = pd.to_datetime(frame[self.date_col], utc=True, errors="coerce")
        frame = frame.dropna(subset=[self.text_col, self.date_col]).sort_values(self.date_col)
        if self.limit:
            frame = frame.head(self.limit)

        previous_time = None
        for record in frame.to_dict("records"):
            text = str(record[self.text_col])
            published_at = record[self.date_col].to_pydatetime()

            if self.speed > 0 and previous_time is not None:
                gap_seconds = (published_at - previous_time).total_seconds()
                time.sleep(max(0.0, gap_seconds / self.speed))
            previous_time = published_at

            meta = {}
            if self.ticker_col and self.ticker_col in record:
                meta["dataset_ticker"] = record[self.ticker_col]

            yield RawDocument(
                doc_id=hashlib.sha1(f"{published_at.isoformat()}{text}".encode()).hexdigest(),
                source=SourceType.TWITTER,
                provider="tweet_replay",
                published_at=published_at,
                text=text,
                meta=meta,
            )
