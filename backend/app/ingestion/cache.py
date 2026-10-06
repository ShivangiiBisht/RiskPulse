import hashlib
import json
import time

import httpx

from app.config import CACHE_DIR, CACHE_TTL_SECONDS, OFFLINE_MODE


def _cache_path(cache_key: str):
    return CACHE_DIR / f"{hashlib.sha1(cache_key.encode()).hexdigest()}.json"


def _read_cache(path):
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def get_json_cached(
    client: httpx.Client,
    url: str,
    params: dict,
    cache_key: str,
    ttl_seconds: int = CACHE_TTL_SECONDS,
    as_text: bool = False,
) -> tuple[dict | list | str | None, bool]:
    """
    Return (payload, from_network).

    - Fresh cache hit: returned without a network call.
    - OFFLINE_MODE: cache only (any age), never touches the network.
    - Network failure: falls back to a stale cache entry if one exists.
    The cache key is explicit so API keys and changing timestamps never leak into it.
    """
    path = _cache_path(cache_key)
    cached = _read_cache(path)

    if cached is not None:
        is_fresh = (time.time() - cached["saved_at"]) < ttl_seconds
        if OFFLINE_MODE or is_fresh:
            return cached["payload"], False
    if OFFLINE_MODE:
        return None, False

    try:
        response = client.get(url, params=params)
        response.raise_for_status()
        payload = response.text if as_text else response.json()
    except (httpx.HTTPError, ValueError):
        return (cached["payload"] if cached else None), False

    path.write_text(
        json.dumps({"saved_at": time.time(), "payload": payload}), encoding="utf-8"
    )
    return payload, True
