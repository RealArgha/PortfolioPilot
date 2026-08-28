# PortfolioPilot — Technical Specification

**AI-Augmented Investment Portfolio Tracker**
Full-stack app: user tracks stock holdings, sees a live dashboard, and can trigger an LLM agent that analyzes the portfolio and exports the analysis as Excel + PowerPoint.

---

## 1. Goal & Scope (1-day MVP)

- User manually adds holdings (ticker, quantity, buy price)
- Backend fetches live/delayed prices and stores daily snapshots
- Dashboard shows allocation, gain/loss, performance over time
- On-demand "Portfolio Analyst" agent: reviews allocation → searches news on top holdings → writes a risk/diversification summary → exports Excel + PPTX
- Every agent run is logged (audit trail)

**Out of scope for MVP:** auth/login (single-user, no accounts), real brokerage integration, real-time WebSocket price streaming, mobile responsiveness polish.

---

## 2. Confirmed Tech Stack

| Layer | Choice | Why |
|---|---|---|
| Frontend | React (Vite) | matches Accenture JD, deploys free on Vercel |
| Backend | FastAPI (Python) | async, matches JD, easy LLM/tool integration |
| Database | PostgreSQL via **Neon** | free tier scales to zero but never deletes data (unlike Render's free Postgres, which is hard-deleted at day 91) |
| ORM | SQLAlchemy | standard, pairs with FastAPI |
| LLM | **Groq** — `llama-3.3-70b-versatile` | free, fast, OpenAI-compatible, supports tool calling + JSON mode, 131k context |
| Market data | **Finnhub** | free tier: 60 calls/min (vs. Alpha Vantage's ~25/day) |
| Excel export | `openpyxl` | |
| PPTX export | `python-pptx` | |
| Backend hosting | **Render** free web service | no card needed; sleeps after 15 min idle, 30–60s cold start — expected, not a bug |
| Frontend hosting | **Vercel** free tier | no cold starts, trivial GitHub deploy |

---

## 3. External API Reference (verified, current)

### 3.1 Groq (LLM)

- Base URL: `https://api.groq.com/openai/v1` (OpenAI SDK-compatible — use `openai` python package, just change `base_url`)
- Auth: `Authorization: Bearer $GROQ_API_KEY`
- Model: `llama-3.3-70b-versatile`
- **Free-tier limits (org-wide, not per-key):** ~30 RPM, ~12,000 TPM, ~1,000 RPD, ~100,000 TPD
- **TPM is the real constraint**, not RPD — a single large prompt (e.g. raw PDF text) can eat a third of the per-minute budget. Chunk/summarize before sending.
- All models support tool/function calling and native JSON mode (`response_format={"type": "json_object"}`)
- On rate-limit: HTTP 429 with a `retry-after` header — implement exponential backoff, don't just crash
- No credit card required to sign up at console.groq.com

### 3.2 Finnhub (market data)

- Base URL: `https://finnhub.io/api/v1`
- Auth: header `X-Finnhub-Token: $FINNHUB_API_KEY` (or `?token=` query param)
- Free tier: **60 calls/minute**, real-time US quotes, company news, basic fundamentals
- Key endpoints:
  - `GET /quote?symbol=AAPL` → `{c: current, h: high, l: low, o: open, pc: prevClose, d: change, dp: changePercent}`
  - `GET /stock/profile2?symbol=AAPL` → company name, industry, market cap, logo
  - `GET /company-news?symbol=AAPL&from=YYYY-MM-DD&to=YYYY-MM-DD` → recent news array (used by the agent's news tool)

---

## 4. Database Schema (Postgres)

```sql
CREATE TABLE holdings (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL,
    quantity NUMERIC NOT NULL,
    buy_price NUMERIC NOT NULL,
    created_at TIMESTAMP DEFAULT now()
);

CREATE TABLE price_snapshots (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL,
    price NUMERIC NOT NULL,
    snapshot_date DATE NOT NULL,
    UNIQUE(ticker, snapshot_date)
);

CREATE TABLE agent_runs (
    id SERIAL PRIMARY KEY,
    status VARCHAR(20) NOT NULL,        -- 'running' | 'success' | 'failed'
    summary TEXT,
    excel_path TEXT,
    pptx_path TEXT,
    started_at TIMESTAMP DEFAULT now(),
    completed_at TIMESTAMP
);
```

---

## 5. Backend API Endpoints (FastAPI)

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/holdings` | add a holding |
| `GET` | `/holdings` | list holdings + live current value (calls Finnhub) |
| `DELETE` | `/holdings/{id}` | remove a holding |
| `GET` | `/portfolio/summary` | total value, allocation %, gain/loss per holding |
| `GET` | `/portfolio/history` | daily snapshot series, for the performance chart |
| `POST` | `/agent/analyze` | triggers the agent run (async — returns a run id immediately) |
| `GET` | `/agent/runs/{id}` | poll run status; once done, returns download links |
| `GET` | `/agent/runs/{id}/excel` | download the generated .xlsx |
| `GET` | `/agent/runs/{id}/pptx` | download the generated .pptx |

---

## 6. Agent Design (tool-calling loop)

Hand-rolled loop (no LangChain/CrewAI) — easier to explain line-by-line in an interview.

```
1. System prompt: "You are a portfolio risk analyst. You have two tools:
   get_portfolio_allocation() and search_news(query). Use them, then
   produce a JSON summary: {overview, risk_flags[], diversification_note,
   top_holdings_commentary[]}."
2. Loop:
   a. Call Groq with messages + tool definitions
   b. If model requests a tool call → execute it locally → append result
      to messages → go to (a)
   c. If model returns final JSON → validate with Pydantic → break
3. Pass validated JSON into the Excel/PPTX generators
4. Save files, update agent_runs row to 'success'
```

Tools exposed to the model:
- `get_portfolio_allocation()` → reads current holdings + Finnhub prices, returns allocation breakdown (local function, no external call from model's perspective)
- `search_news(query: str)` → wraps a web search call, returns top 3 headlines for a holding

---

## 7. Frontend Pages (React)

- `/` — Dashboard: allocation pie chart, holdings table (gain/loss), performance line chart
- `/holdings` — add/remove holdings form
- `/analyze` — "Run Analysis" button → shows agent run status → download links when done

Use **recharts** for charts (already available in this environment; fine to reuse for the actual build too since it's a common, well-supported charting lib).

---

## 8. Environment Variables

```
GROQ_API_KEY=
FINNHUB_API_KEY=
DATABASE_URL=postgresql://...  (from Neon dashboard)
```

Never commit these — `.env` + `.gitignore` from commit #1.

---

## 9. Deployment Steps

**Backend (Render):**
- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT` (must use `$PORT`, not a hardcoded port, or Render reports "no open ports detected")
- Add env vars in Render dashboard (encrypted at rest)
- Expect 30–60s cold start after 15 min idle on free tier — mention this proactively in any live demo

**Frontend (Vercel):**
- Connect GitHub repo, framework preset: Vite
- Set `VITE_API_URL` env var to the Render backend URL

**Database (Neon):**
- Create free Postgres project, copy connection string into `DATABASE_URL`
- Scale-to-zero is fine — it auto-resumes on the next query, doesn't delete data (unlike Render's free Postgres, which hard-deletes at day 91)

---

## 10. Build Order (maps to the earlier 7-day plan, compressed)

1. DB models + FastAPI CRUD for holdings
2. Finnhub integration → `/portfolio/summary`
3. Hand-rolled Groq tool-calling loop (text-only first, no UI)
4. Excel + PPTX generators from the agent's JSON output
5. React dashboard wired to the backend
6. Deploy all three pieces, test end-to-end
7. Record demo, write the 90-second explanation

---

## 11. Known Risks / Open Questions

- Groq's 12K TPM limit may throttle the agent loop if `search_news` results are verbose — truncate news snippets before feeding back to the model
- Render cold start (30–60s) will be visible in any live demo — start the backend URL loading a minute before presenting
- Decide: does `search_news` use a real search API (needs another free-tier key) or a stubbed/mocked news lookup for the MVP? Recommend stubbing with Finnhub's own `/company-news` endpoint instead of adding a third API dependency — same effect, one less key to manage
