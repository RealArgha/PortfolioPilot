import asyncio
import os

import httpx

FINNHUB_BASE_URL = "https://finnhub.io/api/v1"


async def _get_quote(client: httpx.AsyncClient, ticker: str, api_key: str) -> dict | None:
    try:
        resp = await client.get(
            f"{FINNHUB_BASE_URL}/quote",
            params={"symbol": ticker, "token": api_key},
            timeout=10.0,
        )
        resp.raise_for_status()
        data = resp.json()
    except (httpx.HTTPError, ValueError):
        return None

    # Finnhub returns all-zero fields for an unrecognized symbol rather than an error.
    if not data or not data.get("c"):
        return None
    return data


async def get_quotes(tickers: list[str]) -> dict[str, dict | None]:
    """Fetch current quotes for a list of (deduplicated) tickers concurrently.

    Returns a dict mapping ticker -> Finnhub quote dict, or None if the
    quote couldn't be fetched (rate limit, network error, unknown symbol).
    """
    if not tickers:
        return {}

    api_key = os.environ["FINNHUB_API_KEY"]
    async with httpx.AsyncClient() as client:
        results = await asyncio.gather(*(_get_quote(client, t, api_key) for t in tickers))
    return dict(zip(tickers, results))
