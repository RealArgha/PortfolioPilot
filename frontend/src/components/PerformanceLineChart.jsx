import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

function formatCurrency(value) {
  return value.toLocaleString(undefined, { style: "currency", currency: "USD", maximumFractionDigits: 0 });
}

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div
      style={{
        background: "var(--surface-1)",
        border: "1px solid var(--border)",
        borderRadius: 8,
        padding: "8px 12px",
        fontSize: "0.85rem",
      }}
    >
      <div style={{ color: "var(--text-secondary)" }}>{label}</div>
      <strong>{formatCurrency(payload[0].value)}</strong>
    </div>
  );
}

export default function PerformanceLineChart({ history }) {
  if (history.length === 0) {
    return (
      <div className="empty-state">
        No history yet — snapshots are recorded automatically each day you open this
        dashboard. Check back tomorrow to see a trend line.
      </div>
    );
  }

  const data = history.map((p) => ({ date: p.date, value: Number(p.total_value) }));

  return (
    <ResponsiveContainer width="100%" height={280}>
      <LineChart data={data} margin={{ top: 8, right: 16, bottom: 0, left: 0 }}>
        <CartesianGrid stroke="var(--gridline)" vertical={false} />
        <XAxis
          dataKey="date"
          stroke="var(--baseline)"
          tick={{ fill: "var(--muted)", fontSize: 12 }}
          tickLine={false}
        />
        <YAxis
          stroke="var(--baseline)"
          tick={{ fill: "var(--muted)", fontSize: 12 }}
          tickLine={false}
          tickFormatter={formatCurrency}
          width={80}
        />
        <Tooltip content={<CustomTooltip />} />
        <Line
          type="monotone"
          dataKey="value"
          stroke="var(--series-1)"
          strokeWidth={2}
          dot={{ r: 3, fill: "var(--series-1)" }}
          activeDot={{ r: 5 }}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
