"""Generate the synthetic datasets in /data (reproducible, seed=42).

  python backend/scripts/generate_data.py

Outputs
  data/portfolio.csv      synthetic wholesale-banking book (loans, bonds, derivatives, equity)
  data/sample_tweets.csv  small synthetic stock-tweet sample (same columns as the Kaggle dataset)
Nothing here is real client data.
"""
import csv
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.entities import SECTORS, TICKER_ALIASES  # noqa: E402

OUT = Path(__file__).resolve().parents[2] / "data"
rng = random.Random(42)
TICKERS = list(TICKER_ALIASES)
NAMES = {t: aliases[0].title() for t, aliases in TICKER_ALIASES.items()}
NAMES.update({"JPM": "JPMorgan", "GS": "Goldman Sachs", "BAC": "Bank of America", "C": "Citigroup",
              "WFC": "Wells Fargo", "XOM": "Exxon", "JNJ": "Johnson & Johnson", "KO": "Coca-Cola",
              "META": "Meta Platforms", "NVDA": "Nvidia", "AAPL": "Apple", "GOOGL": "Google"})
PD_BY_RATING = {"AA": 0.0004, "A": 0.0008, "BBB": 0.002, "BB": 0.01, "B": 0.04}


def build_portfolio() -> list[dict]:
    rows = []

    def add(kind, subtype, **fields):
        base = {"asset_type": kind, "subtype": subtype, "counterparty": "", "ticker": "", "sector": "",
                "rating": "", "notional_musd": 0, "market_value_musd": 0, "duration": 0,
                "convexity": 0, "pd": 0, "lgd": 0, "delta": 0, "direction": 0}
        base.update(fields)
        base["asset_id"] = f"{kind[:3].upper()}-{len(rows) + 1:03d}"
        rows.append(base)

    for index in range(20):
        ticker, rating = rng.choice(TICKERS), rng.choice(["A", "BBB", "BBB", "BB", "B"])
        notional, pd = round(rng.uniform(20, 120), 1), PD_BY_RATING[rating] * rng.uniform(0.8, 1.5)
        add("loan", "term_loan", counterparty=f"Corporate Borrower {index + 1:02d}", ticker=ticker,
            sector=SECTORS[ticker], rating=rating, notional_musd=notional, pd=round(pd, 5), lgd=0.45,
            market_value_musd=round(notional * (1 - pd * 0.45), 2))
    for index in range(18):
        ticker, rating = rng.choice(TICKERS), rng.choice(["AA", "A", "A", "BBB", "BBB", "BB"])
        notional, duration = round(rng.uniform(15, 90), 1), round(rng.uniform(2, 11), 2)
        add("bond", "corporate_bond", counterparty=f"Issuer {NAMES[ticker]}", ticker=ticker,
            sector=SECTORS[ticker], rating=rating, notional_musd=notional, duration=duration,
            convexity=round(duration**2 * 0.9, 2), market_value_musd=round(notional * rng.uniform(0.94, 1.04), 2))
    for index in range(5):
        ticker, notional = rng.choice(TICKERS), round(rng.uniform(10, 60), 1)
        add("derivative", "equity_swap", counterparty=f"Dealer {index + 1:02d}", ticker=ticker,
            sector=SECTORS[ticker], rating="A", notional_musd=notional, delta=round(rng.uniform(0.4, 0.9), 2),
            market_value_musd=round(notional * rng.uniform(-0.02, 0.04), 2))
    for index in range(5):
        notional = round(rng.uniform(50, 200), 1)
        add("derivative", "ir_swap", counterparty=f"Dealer {index + 6:02d}", rating="A", notional_musd=notional,
            duration=round(rng.uniform(3, 8), 2), direction=rng.choice([1, -1]),
            market_value_musd=round(notional * rng.uniform(-0.015, 0.015), 2))
    for index in range(12):
        ticker, value = rng.choice(TICKERS), round(rng.uniform(15, 80), 1)
        add("equity", "cash_equity", counterparty=f"Trading Book {index + 1:02d}", ticker=ticker,
            sector=SECTORS[ticker], notional_musd=value, market_value_musd=value)
    return rows


POSITIVE = ["{c} beats earnings estimates and raises guidance on strong demand",
            "{c} shares surge after record quarter", "Analysts upgrade {c} on strong growth outlook",
            "{c} announces buyback and dividend increase", "{c} unveils new product lineup, demand looks strong"]
NEGATIVE = ["{c} shares tumble after profit warning", "{c} faces regulatory probe and possible fine",
            "Downgrade risk for {c} as losses widen", "{c} cuts outlook amid weak demand",
            "{c} hit by lawsuit, shares slide"]
NEUTRAL = ["{c} to present at industry conference next week", "Watching {c} ahead of the open",
           "{c} sets date for quarterly results call"]
MACRO = ["Fed signals more interest rate hikes as inflation stays hot",
         "Oil prices surge as geopolitical tensions escalate",
         "Markets fear recession as jobs data disappoints", "New sanctions announced, markets tumble",
         "Treasury yields jump as central bank warns on inflation"]
CREDIT_STORY = ["{c} downgrade risk grows as loan losses and default fears spread across banks",
                "Bank run fears: {c} shares tumble on liquidity crisis worries",
                "{c} warns of rising credit losses, creditors turn cautious"]


def build_tweets() -> list[dict]:
    start = datetime(2026, 10, 12, tzinfo=timezone.utc)
    mood = {t: rng.uniform(-0.5, 0.5) for t in TICKERS}
    rows = []

    def add(when, text, ticker=""):
        rows.append({"Date": when.strftime("%Y-%m-%d %H:%M:%S+00:00"), "Tweet": text,
                     "Stock Name": ticker, "Company Name": NAMES.get(ticker, "")})

    for ticker in TICKERS:
        for _ in range(9):
            when = start + timedelta(minutes=rng.randint(0, 7 * 24 * 60 - 1))
            roll = rng.random() - mood[ticker] * 0.5
            pool = POSITIVE if roll < 0.35 else NEGATIVE if roll > 0.65 else NEUTRAL
            text = rng.choice(pool).format(c=NAMES[ticker])
            add(when, f"${ticker} {text}" if rng.random() < 0.5 else text, ticker)
    for _ in range(14):
        add(start + timedelta(minutes=rng.randint(0, 7 * 24 * 60 - 1)), rng.choice(MACRO))
    story_start = start + timedelta(days=4, hours=14)  # Oct 16: a banking credit scare
    for offset, ticker in enumerate(["JPM", "GS", "BAC", "C", "WFC", "JPM", "GS"]):
        add(story_start + timedelta(minutes=25 * offset), rng.choice(CREDIT_STORY).format(c=NAMES[ticker]), ticker)
    rows.sort(key=lambda r: r["Date"])
    return rows


def write_csv(path: Path, rows: list[dict]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {path} ({len(rows)} rows)")


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    portfolio = build_portfolio()
    order = ["asset_id", "asset_type", "subtype", "counterparty", "ticker", "sector", "rating",
             "notional_musd", "market_value_musd", "duration", "convexity", "pd", "lgd", "delta", "direction"]
    write_csv(OUT / "portfolio.csv", [{k: row[k] for k in order} for row in portfolio])
    write_csv(OUT / "sample_tweets.csv", build_tweets())
