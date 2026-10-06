import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

DATA_DIR = Path(os.getenv("DATA_DIR", BASE_DIR / "data"))
CACHE_DIR = DATA_DIR / "cache"
DB_PATH = DATA_DIR / "risk_engine.db"
TWEETS_CSV_PATH = Path(os.getenv("TWEETS_CSV_PATH", DATA_DIR / "stock_tweets.csv"))

FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY", "")
OFFLINE_MODE = os.getenv("OFFLINE_MODE", "0") == "1"
CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "900"))
FRONTEND_ORIGINS = os.getenv("FRONTEND_ORIGINS", "http://localhost:3000").split(",")

for directory in (DATA_DIR, CACHE_DIR):
    directory.mkdir(parents=True, exist_ok=True)
