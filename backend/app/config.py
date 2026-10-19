import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent  # backend/
REPO_DIR = BASE_DIR.parent
load_dotenv(BASE_DIR / ".env")

DATA_DIR = Path(os.getenv("DATA_DIR", BASE_DIR / "data"))  # runtime: SQLite DB + API cache
CACHE_DIR = DATA_DIR / "cache"
DB_PATH = DATA_DIR / "risk_engine.db"
INPUT_DIR = Path(os.getenv("INPUT_DIR", REPO_DIR / "data"))  # committed inputs (portfolio, shocks, samples)


def _find_tweets_csv() -> Path:
    override = os.getenv("TWEETS_CSV_PATH")
    if override and Path(override).exists():
        return Path(override)
    for candidate in (
        DATA_DIR / "stock_tweets.csv",  # full Kaggle dataset (git-ignored)
        INPUT_DIR / "stock_tweets.csv",
        INPUT_DIR / "sample_tweets.csv",  # small synthetic sample shipped in the repo
    ):
        if candidate.exists():
            return candidate
    return INPUT_DIR / "sample_tweets.csv"


TWEETS_CSV_PATH = _find_tweets_csv()

FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY", "")
OFFLINE_MODE = os.getenv("OFFLINE_MODE", "0") == "1"
CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "900"))
FRONTEND_ORIGINS = os.getenv(
    "FRONTEND_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000"
).split(",")

SENTIMENT_BACKEND = os.getenv("SENTIMENT_BACKEND", "auto")  # auto | finbert | lexicon
EVENT_BACKEND = os.getenv("EVENT_BACKEND", "rules")  # rules | zeroshot

for directory in (DATA_DIR, CACHE_DIR):
    directory.mkdir(parents=True, exist_ok=True)
