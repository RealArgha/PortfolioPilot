import asyncio
import os
from datetime import date, timedelta

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


async def get_company_news(ticker: str, limit: int = 3, lookback_days: int = 14) -> list[dict]:
    """Top recent headlines for a ticker, truncated to stay cheap on Groq's TPM budget."""
    api_key = os.environ["FINNHUB_API_KEY"]
    to_date = date.today()
    from_date = to_date - timedelta(days=lookback_days)

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{FINNHUB_BASE_URL}/company-news",
                params={
                    "symbol": ticker,
                    "from": from_date.isoformat(),
                    "to": to_date.isoformat(),
                    "token": api_key,
                },
                timeout=10.0,
            )
            resp.raise_for_status()
            articles = resp.json()
    except (httpx.HTTPError, ValueError):
        return []

    if not isinstance(articles, list):
        return []

    return [
        {
            "headline": (article.get("headline") or "")[:200],
            "summary": (article.get("summary") or "")[:300],
            "source": article.get("source"),
        }
        for article in articles[:limit]
    ]
