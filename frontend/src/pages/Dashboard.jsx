import { useEffect, useState } from "react";
import { api } from "../api";
import AllocationPieChart from "../components/AllocationPieChart";
import PerformanceLineChart from "../components/PerformanceLineChart";
import HoldingsTable from "../components/HoldingsTable";

function formatCurrency(value) {
  return Number(value).toLocaleString(undefined, { style: "currency", currency: "USD" });
}

function formatPct(value) {
  if (value === null || value === undefined) return "—";
  return `${Number(value) >= 0 ? "+" : ""}${Number(value).toFixed(2)}%`;
}

export default function Dashboard() {
  const [summary, setSummary] = useState(null);
  const [history, setHistory] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    Promise.all([api.getSummary(), api.getHistory()])
      .then(([summaryData, historyData]) => {
        setSummary(summaryData);
        setHistory(historyData);
      })
      .catch((err) => setError(err.message));
  }, []);

  if (error) {
    return (
      <div className="page">
        <div className="error-banner">Failed to load dashboard: {error}</div>
      </div>
    );
  }

  if (!summary || !history) {
    return (
      <div className="page">
        <div className="empty-state">Loading…</div>
      </div>
    );
  }

  const gainPositive = Number(summary.total_gain_loss) >= 0;

  return (
    <div className="page">
      <h1>Dashboard</h1>

      <div className="stat-grid">
        <div className="stat-tile">
          <div className="label">Total Value</div>
          <div className="value">{formatCurrency(summary.total_market_value)}</div>
        </div>
        <div className="stat-tile">
          <div className="label">Cost Basis</div>
          <div className="value">{formatCurrency(summary.total_cost_basis)}</div>
        </div>
        <div className="stat-tile">
          <div className="label">Gain / Loss</div>
          <div className={`value ${gainPositive ? "up" : "down"}`}>
            {formatCurrency(summary.total_gain_loss)}
          </div>
        </div>
        <div className="stat-tile">
          <div className="label">Gain / Loss %</div>
          <div className={`value ${gainPositive ? "up" : "down"}`}>
            {formatPct(summary.total_gain_loss_pct)}
          </div>
        </div>
      </div>

      <div className="two-col">
        <div className="card">
          <h2>Allocation</h2>
          <AllocationPieChart holdings={summary.holdings} />
        </div>
        <div className="card">
          <h2>Performance</h2>
          <PerformanceLineChart history={history} />
        </div>
      </div>

      <div className="card">
        <h2>Holdings</h2>
        <HoldingsTable holdings={summary.holdings} />
      </div>
    </div>
  );
}
