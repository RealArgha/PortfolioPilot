import asyncio
import json
import os
import time
from decimal import Decimal

from openai import OpenAI, RateLimitError
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.services import finnhub, portfolio

GROQ_BASE_URL = "https://api.groq.com/openai/v1"
MODEL = "llama-3.3-70b-versatile"
MAX_TOOL_ITERATIONS = 6

SYSTEM_PROMPT = """You are a portfolio risk analyst. You have two tools: \
get_portfolio_allocation() and search_news(query). Use them as needed to \
research the portfolio, then respond with ONLY a JSON object (no markdown \
fences, no commentary before or after) matching exactly this shape:
{
  "overview": "string",
  "risk_flags": ["string", ...],
  "diversification_note": "string",
  "top_holdings_commentary": [{"ticker": "string", "commentary": "string"}, ...]
}"""

USER_PROMPT = "Analyze my current portfolio for risk and diversification."

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_portfolio_allocation",
            "description": (
                "Returns the current portfolio's holdings with live prices, "
                "cost basis, market value, gain/loss %, and allocation % per ticker."
            ),
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_news",
            "description": "Returns the 3 most recent news headlines for a given stock ticker.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Stock ticker symbol, e.g. AAPL"},
                },
                "required": ["query"],
            },
        },
    },
]


class TopHoldingCommentary(BaseModel):
    ticker: str
    commentary: str


class AgentAnalysis(BaseModel):
    overview: str
    risk_flags: list[str]
    diversification_note: str
    top_holdings_commentary: list[TopHoldingCommentary]


def get_client() -> OpenAI:
    return OpenAI(base_url=GROQ_BASE_URL, api_key=os.environ["GROQ_API_KEY"])


async def _tool_get_portfolio_allocation(db: Session) -> dict:
    enriched = await portfolio.get_enriched_holdings(db)
    total_market_value = sum(
        (e.market_value for e in enriched if e.market_value is not None), Decimal("0")
    )
    return {
        "holdings": [
            {
                "ticker": e.holding.ticker,
                "quantity": str(e.holding.quantity),
                "buy_price": str(e.holding.buy_price),
                "current_price": str(e.current_price) if e.current_price is not None else None,
                "gain_loss_pct": str(e.gain_loss_pct) if e.gain_loss_pct is not None else None,
                "allocation_pct": (
                    str(e.market_value / total_market_value * 100)
                    if e.market_value is not None and total_market_value > 0
                    else None
                ),
            }
            for e in enriched
        ]
    }


async def _tool_search_news(ticker: str) -> dict:
    headlines = await finnhub.get_company_news(ticker, limit=3)
    return {"ticker": ticker, "headlines": headlines}


async def _execute_tool(db: Session, name: str, arguments: dict) -> dict:
    if name == "get_portfolio_allocation":
        return await _tool_get_portfolio_allocation(db)
    if name == "search_news":
        return await _tool_search_news(str(arguments.get("query", "")))
    return {"error": f"unknown tool: {name}"}


def _call_groq_with_backoff(client: OpenAI, messages: list[dict], max_retries: int = 5):
    delay = 2.0
    for attempt in range(max_retries):
        try:
            return client.chat.completions.create(model=MODEL, messages=messages, tools=TOOLS)
        except RateLimitError as exc:
            if attempt == max_retries - 1:
                raise
            retry_after = delay
            response = getattr(exc, "response", None)
            header_val = response.headers.get("retry-after") if response is not None else None
            if header_val:
                try:
                    retry_after = float(header_val)
                except ValueError:
                    pass
            time.sleep(retry_after)
            delay *= 2
    raise RuntimeError("unreachable")  # pragma: no cover


def _parse_analysis(content: str) -> AgentAnalysis:
    text = (content or "").strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
        text = text.strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"model did not return valid JSON: {exc}\n---\n{content}") from exc
    return AgentAnalysis.model_validate(data)


async def run_analysis(db: Session, client: OpenAI | None = None) -> AgentAnalysis:
    client = client or get_client()
    messages: list[dict] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": USER_PROMPT},
    ]

    for _ in range(MAX_TOOL_ITERATIONS):
        response = await asyncio.to_thread(_call_groq_with_backoff, client, messages)
        message = response.choices[0].message

        if message.tool_calls:
            messages.append(
                {
                    "role": "assistant",
                    "content": message.content,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                        }
                        for tc in message.tool_calls
                    ],
                }
            )
            for tool_call in message.tool_calls:
                try:
                    arguments = json.loads(tool_call.function.arguments or "{}")
                except json.JSONDecodeError:
                    arguments = {}
                result = await _execute_tool(db, tool_call.function.name, arguments)
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(result),
                    }
                )
            continue

        return _parse_analysis(message.content or "")

    raise RuntimeError("agent exceeded max tool iterations without a final answer")
