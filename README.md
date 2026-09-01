# PortfolioPilot

AI-augmented investment portfolio tracker. Track stock holdings, see a live
dashboard, and trigger an LLM agent that reviews your allocation, checks
recent news on your top holdings, and exports a risk/diversification report
as Excel and PowerPoint.

Single-user MVP — no auth/accounts, no real brokerage integration.

## How it works

1. You add holdings (ticker, quantity, buy price) through the API/UI.
2. The backend fetches live prices from Finnhub and computes allocation,
   gain/loss, and portfolio value.
3. On demand, a hand-rolled tool-calling loop sends the portfolio to Groq's
   `openai/gpt-oss-120b`. The model can call two local tools —
   `get_portfolio_allocation()` and `search_news(ticker)` — before returning
   a structured JSON risk analysis.
4. That analysis is validated (Pydantic) and exported to `.xlsx` / `.pptx`.
5. Every run is logged to `agent_runs` for an audit trail.

No LangChain/CrewAI — the agent loop is ~150 lines of plain Python so it's
easy to read and explain end-to-end.

## Tech stack

| Layer | Choice |
|---|---|
| Frontend | React (Vite) |
| Backend | FastAPI (Python, async) |
| Database | PostgreSQL via [Neon](https://neon.tech) (free tier, scale-to-zero) |
| ORM | SQLAlchemy |
| LLM | [Groq](https://console.groq.com) — `openai/gpt-oss-120b`, OpenAI-compatible API |
| Market data | [Finnhub](https://finnhub.io) — quotes + company news |
| Excel export | `openpyxl` |
| PPTX export | `python-pptx` |
| Backend hosting | Render (free web service) |
| Frontend hosting | Vercel (free tier) |

Full design rationale and API reference: [`docs/SPEC.md`](docs/SPEC.md).

## Project status

- [x] DB models + FastAPI CRUD for holdings
- [x] Finnhub integration → `/portfolio/summary`, live pricing on `/holdings`
- [x] Hand-rolled Groq tool-calling loop (verified end-to-end against real Groq/Finnhub/Neon)
- [x] Excel + PPTX generators, `/agent/analyze` + `/agent/runs/{id}` endpoints
- [x] React dashboard (`/`, `/holdings`, `/analyze`)
- [ ] Deploy (Render + Vercel + Neon)
- [ ] Demo recording

## Repo layout

```
backend/
  main.py                    # FastAPI app entrypoint (uvicorn main:app)
  app/
    database.py               # SQLAlchemy engine/session
    models.py                 # Holding, PriceSnapshot, AgentRun
    schemas.py                # Pydantic request/response models
    routers/
      holdings.py              # POST/GET/DELETE /holdings
      portfolio.py             # GET /portfolio/summary
      agent.py                  # POST /agent/analyze, GET /agent/runs/{id}(/excel|/pptx)
    services/
      finnhub.py                # quotes + company news client
      portfolio.py               # valuation/allocation logic (shared)
      agent.py                   # Groq tool-calling loop
      exports.py                 # Excel/PPTX generation from AgentAnalysis
frontend/
  src/
    api.js                     # fetch wrapper, base URL from VITE_API_URL
    App.jsx                    # routes + nav
    pages/                     # Dashboard, Holdings, Analyze
    components/                # HoldingsTable, AllocationPieChart, PerformanceLineChart
docs/
  SPEC.md                     # full technical spec
```

## Running the backend locally

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env   # then fill in the three keys below
uvicorn main:app --reload --port 8000
```

`GET /health` should return `{"status": "ok"}`. Interactive API docs are
served at `/docs`.

### Environment variables (`backend/.env`)

```
GROQ_API_KEY=       # console.groq.com — free, no card required
FINNHUB_API_KEY=    # finnhub.io — free tier, 60 calls/min
DATABASE_URL=       # postgresql://... from your Neon project
```

`DATABASE_URL` also works with a local SQLite string
(`sqlite:///./dev.db`) for quick testing without a real Postgres instance —
the same SQLAlchemy models work against either.

## Running the frontend locally

```bash
cd frontend
npm install
cp .env.example .env   # VITE_API_URL, defaults to http://localhost:8000
npm run dev
```

## API endpoints

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/holdings` | Add a holding |
| `GET` | `/holdings` | List holdings with live price, market value, gain/loss |
| `DELETE` | `/holdings/{id}` | Remove a holding |
| `GET` | `/portfolio/summary` | Total value, allocation %, gain/loss |
| `GET` | `/portfolio/history` | Daily total-value series (snapshots recorded as a side effect of `/portfolio/summary`) |
| `POST` | `/agent/analyze` | Trigger an agent run — returns the run id immediately, runs in the background |
| `GET` | `/agent/runs/{id}` | Poll run status; returns `excel_url`/`pptx_url` once done |
| `GET` | `/agent/runs/{id}/excel` | Download the generated `.xlsx` |
| `GET` | `/agent/runs/{id}/pptx` | Download the generated `.pptx` |

## Deployment

- **Neon** — create a free Postgres project, copy the connection string into `DATABASE_URL`.
- **Render** — build: `pip install -r requirements.txt`; start: `uvicorn main:app --host 0.0.0.0 --port $PORT`. Free tier sleeps after 15 min idle (30–60s cold start).
- **Vercel** — connect the repo, Vite preset, set `VITE_API_URL` to the Render backend URL.

## Known limitations

- Groq free tier is ~12K TPM — `search_news` results are truncated before being fed back to the model to stay under budget.
- If a Finnhub quote fails (rate limit, bad symbol, network error), that holding's price/value comes back `null` rather than failing the whole request — but it's also excluded from portfolio totals, which can understate `total_market_value` when quotes are partially missing.
- Render's cold start is visible in a live demo — worth loading the backend URL a minute before presenting.
