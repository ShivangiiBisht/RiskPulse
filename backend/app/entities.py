import re

# Extend to your 10-20 index stocks. First alias is used as the search query.
TICKER_ALIASES: dict[str, list[str]] = {
    "AAPL": ["apple", "iphone"],
    "MSFT": ["microsoft", "azure"],
    "GOOGL": ["google", "alphabet", "youtube"],
    "AMZN": ["amazon", "aws"],
    "META": ["meta platforms", "facebook", "instagram"],
    "NVDA": ["nvidia"],
    "TSLA": ["tesla"],
    "JPM": ["jpmorgan", "jp morgan"],
    "GS": ["goldman sachs", "goldman"],
    "BAC": ["bank of america"],
    "C": ["citigroup", "citibank"],
    "WFC": ["wells fargo"],
    "XOM": ["exxon", "exxonmobil"],
    "CVX": ["chevron"],
    "JNJ": ["johnson & johnson", "johnson and johnson"],
    "PFE": ["pfizer"],
    "WMT": ["walmart"],
    "KO": ["coca-cola", "coca cola"],
}

MACRO_QUERIES = ["interest rates", "sanctions", "bank default", "oil prices"]

COMPANY_QUERIES = [aliases[0] for aliases in TICKER_ALIASES.values()]


def _build_pattern(ticker: str, aliases: list[str]) -> re.Pattern:
    names = list(aliases)
    if len(ticker) >= 3:  # short tickers ("C", "KO", "GS") would match ordinary words
        names.append(ticker.lower())
    alternatives = "|".join(re.escape(name) for name in names)
    return re.compile(rf"(?<!\w)(?:{alternatives})(?!\w)", re.IGNORECASE)


_PATTERNS = {ticker: _build_pattern(ticker, aliases) for ticker, aliases in TICKER_ALIASES.items()}
_CASHTAG = re.compile(r"\$([A-Za-z]{1,5})\b")


def extract_tickers(text: str) -> list[str]:
    found = {ticker for ticker, pattern in _PATTERNS.items() if pattern.search(text)}
    found |= {tag.upper() for tag in _CASHTAG.findall(text) if tag.upper() in TICKER_ALIASES}
    return sorted(found)


def normalize_ticker(value) -> str | None:
    """Map a dataset-provided ticker column value to a known ticker, else None."""
    if value is None:
        return None
    candidate = str(value).strip().upper().lstrip("$")
    return candidate if candidate in TICKER_ALIASES else None
