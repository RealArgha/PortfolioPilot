import { Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";

const SERIES_COLORS = [
  "var(--series-1)",
  "var(--series-2)",
  "var(--series-3)",
  "var(--series-4)",
  "var(--series-5)",
  "var(--series-6)",
  "var(--series-7)",
  "var(--series-8)",
];
const MAX_SLICES = 8;

function formatCurrency(value) {
  return value.toLocaleString(undefined, { style: "currency", currency: "USD" });
}

function buildSlices(holdings) {
  const priced = holdings
    .filter((h) => h.market_value !== null)
    .map((h) => ({ name: h.ticker, value: Number(h.market_value) }))
    .sort((a, b) => b.value - a.value);

  if (priced.length <= MAX_SLICES) return priced;

  const head = priced.slice(0, MAX_SLICES - 1);
  const otherValue = priced.slice(MAX_SLICES - 1).reduce((sum, s) => sum + s.value, 0);
  return [...head, { name: "Other", value: otherValue }];
}

function CustomTooltip({ active, payload }) {
  if (!active || !payload?.length) return null;
  const { name, value } = payload[0];
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
      <strong>{name}</strong>
      <div style={{ color: "var(--text-secondary)" }}>{formatCurrency(value)}</div>
    </div>
  );
}

export default function AllocationPieChart({ holdings }) {
  const slices = buildSlices(holdings);

  if (slices.length === 0) {
    return <div className="empty-state">No priced holdings yet.</div>;
  }

  return (
    <ResponsiveContainer width="100%" height={280}>
      <PieChart>
        <Pie
          data={slices}
          dataKey="value"
          nameKey="name"
          innerRadius={60}
          outerRadius={100}
          paddingAngle={2}
          label={({ percent }) => (percent >= 0.08 ? `${Math.round(percent * 100)}%` : "")}
        >
          {slices.map((slice, i) => (
            <Cell
              key={slice.name}
              fill={slice.name === "Other" ? "var(--series-other)" : SERIES_COLORS[i % SERIES_COLORS.length]}
              stroke="var(--surface-1)"
              strokeWidth={2}
            />
          ))}
        </Pie>
        <Tooltip content={<CustomTooltip />} />
        <Legend wrapperStyle={{ fontSize: "0.85rem", color: "var(--text-secondary)" }} />
      </PieChart>
    </ResponsiveContainer>
  );
}
