# Risk Engine backend (ingestion stage)

```
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # optional: add FINNHUB_API_KEY
uvicorn app.main:app --reload
```

Put the Kaggle tweets CSV at `data/stock_tweets.csv`.

Endpoints: POST /ingest/gdelt | /ingest/googlenews | /ingest/finnhub | /ingest/tweets | /ingest/all,
GET /ingest/jobs, /documents, /stats, /tickers, /health. Docs at /docs.

Set `OFFLINE_MODE=1` to serve only cached API responses (data/cache) for a safe demo.
