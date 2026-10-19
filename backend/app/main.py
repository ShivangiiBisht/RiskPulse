from datetime import datetime, timezone
from typing import Callable

from fastapi import BackgroundTasks, FastAPI, HTTPException, Query
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

from app.config import FINNHUB_API_KEY, FRONTEND_ORIGINS, OFFLINE_MODE, TWEETS_CSV_PATH
from app.db import get_stats, list_documents, list_signals
from app.engine import rebalancer, sandbox, stress
from app.engine.events import EVENT_TYPES
from app.engine.scoring import score_pending
from app.entities import COMPANY_QUERIES, MACRO_QUERIES, SECTORS, TICKER_ALIASES
from app.ingestion.base import BaseSource
from app.ingestion.finnhub_news import FinnhubNewsSource
from app.ingestion.gdelt_doc import GdeltDocSource
from app.ingestion.google_news_rss import GoogleNewsRssSource
from app.ingestion.pipeline import run_ingestion
from app.ingestion.tweets_replay import TweetReplaySource

app = FastAPI(title="Risk Engine API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

JOBS: dict[str, dict] = {}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _run_job(job_name: str, source_factory: Callable[[], BaseSource]) -> None:
    JOBS[job_name] = {"status": "running", "started_at": _now()}
    try:
        stats = run_ingestion(source_factory())
        stats["scoring"] = score_pending()  # turn new documents into risk signals right away
        JOBS[job_name] = {"status": "done", "finished_at": _now(), "stats": stats}
    except Exception as error:  # surface any failure through /ingest/jobs
        JOBS[job_name] = {"status": "failed", "finished_at": _now(), "error": repr(error)}


def _start_job(
    background_tasks: BackgroundTasks,
    job_name: str,
    source_factory: Callable[[], BaseSource],
) -> dict:
    if JOBS.get(job_name, {}).get("status") == "running":
        return {"job": job_name, "status": "already running"}
    JOBS[job_name] = {"status": "queued", "queued_at": _now()}
    background_tasks.add_task(_run_job, job_name, source_factory)
    return {"job": job_name, "status": "queued"}


@app.get("/health")
def health():
    return {"status": "ok", "offline_mode": OFFLINE_MODE}


@app.get("/tickers")
def tickers():
    return {t: {"aliases": aliases, "sector": SECTORS.get(t)} for t, aliases in TICKER_ALIASES.items()}


@app.get("/event-types")
def event_types():
    return EVENT_TYPES


@app.post("/ingest/finnhub")
def ingest_finnhub(background_tasks: BackgroundTasks, lookback_days: int = 3):
    return _start_job(
        background_tasks, "finnhub", lambda: FinnhubNewsSource(lookback_days=lookback_days)
    )


@app.post("/ingest/googlenews")
def ingest_google_news(background_tasks: BackgroundTasks, recency: str = "1d"):
    queries = [f"{query} stock" for query in COMPANY_QUERIES] + MACRO_QUERIES
    return _start_job(
        background_tasks, "googlenews", lambda: GoogleNewsRssSource(queries, recency)
    )


@app.post("/ingest/gdelt")
def ingest_gdelt(background_tasks: BackgroundTasks, timespan: str = "1d"):
    return _start_job(
        background_tasks,
        "gdelt",
        lambda: GdeltDocSource(COMPANY_QUERIES + MACRO_QUERIES, timespan),
    )


@app.post("/ingest/tweets")
def ingest_tweets(
    background_tasks: BackgroundTasks,
    speed: float = Query(0.0, ge=0, description="Simulated seconds per real second; 0 = bulk load"),
    limit: int | None = Query(5000, ge=1),
):
    return _start_job(
        background_tasks,
        "tweets",
        lambda: TweetReplaySource(TWEETS_CSV_PATH, speed=speed, limit=limit),
    )


@app.post("/ingest/all")
def ingest_all(background_tasks: BackgroundTasks):
    jobs = [
        ingest_gdelt(background_tasks, timespan="1d"),
        ingest_google_news(background_tasks, recency="1d"),
        ingest_tweets(background_tasks, speed=0.0, limit=5000),
    ]
    if FINNHUB_API_KEY or OFFLINE_MODE:
        jobs.append(ingest_finnhub(background_tasks, lookback_days=3))
    return jobs


@app.get("/ingest/jobs")
def ingest_jobs():
    return JOBS


@app.get("/documents")
def documents(
    ticker: str | None = None,
    source: str | None = None,
    provider: str | None = None,
    since: str | None = Query(None, description="ISO timestamp lower bound"),
    unscored_only: bool = False,
    limit: int = Query(50, ge=1, le=500),
):
    return list_documents(ticker, source, provider, since, unscored_only, limit)


@app.get("/stats")
def stats():
    return get_stats()


# ------------------------------------------------------------ Risk Engine output
@app.post("/engine/score")
def engine_score(background_tasks: BackgroundTasks):
    """Score any documents that are still unscored (normally done automatically after ingestion)."""
    def job():
        JOBS["scoring"] = {"status": "running", "started_at": _now()}
        JOBS["scoring"] = {"status": "done", "finished_at": _now(), "stats": {"scoring": score_pending()}}

    background_tasks.add_task(job)
    return {"job": "scoring", "status": "queued"}


@app.get("/signals")
def signals(
    ticker: str | None = None,
    event_type: str | None = None,
    min_impact: int = Query(1, ge=1, le=10),
    provider: str | None = None,
    since: str | None = None,
    limit: int = Query(100, ge=1, le=1000),
):
    """Structured risk signals: sentiment [-1,1], event type, impact [1,10], evidence and score breakdown."""
    return list_signals(ticker, event_type, min_impact, provider, since, limit)


# ----------------------------------------------------------- Module A: rebalancer
@app.get("/rebalance/current")
def rebalance_current():
    return rebalancer.current_snapshot()


@app.get("/rebalance/timeline")
def rebalance_timeline(max_points: int = Query(60, ge=2, le=200)):
    return rebalancer.timeline(max_points)


# --------------------------------------------------------- Module B: stress test
class StressRequest(BaseModel):
    event_type: str
    impact: int = 8
    tickers: list[str] = []
    headline: str | None = None


@app.get("/stress/auto")
def stress_auto(threshold: int = Query(stress.TRIGGER_IMPACT, ge=1, le=10)):
    return stress.auto_trigger(threshold)


@app.post("/stress/run")
def stress_run(request: StressRequest):
    return stress.run_stress(request.event_type, request.impact, request.tickers, request.headline)


# ------------------------------------------------------------------ what-if sandbox
class HeadlineRequest(BaseModel):
    text: str


@app.get("/sandbox/scenarios")
def sandbox_scenarios():
    return sandbox.load_scenarios()


@app.post("/sandbox/headline")
def sandbox_headline(request: HeadlineRequest):
    if len(request.text.strip()) < 10:
        raise HTTPException(status_code=422, detail="Headline is too short")
    return sandbox.inject_headline(request.text)


@app.post("/sandbox/scenario/{scenario_id}")
def sandbox_scenario(scenario_id: str):
    report = sandbox.run_scenario(scenario_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Unknown scenario")
    return report


@app.post("/sandbox/reset")
def sandbox_reset():
    return sandbox.reset()
