# PortfolioPilot frontend

React (Vite) dashboard for PortfolioPilot. See the [root README](../README.md)
for the full project overview, and [`docs/SPEC.md`](../docs/SPEC.md) for the
design spec.

## Local development

```bash
npm install
cp .env.example .env   # set VITE_API_URL if the backend isn't on localhost:8000
npm run dev
```

## Pages

- `/` — Dashboard: stat tiles, allocation pie chart, performance line chart, holdings table
- `/holdings` — Add/remove holdings
- `/analyze` — Trigger a Portfolio Analyst run and download the Excel/PPTX export

## Build

```bash
npm run build   # outputs to dist/
```
