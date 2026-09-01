function formatCurrency(value) {
  if (value === null || value === undefined) return "—";
  return Number(value).toLocaleString(undefined, { style: "currency", currency: "USD" });
}

function formatPct(value) {
  if (value === null || value === undefined) return "—";
  return `${Number(value) >= 0 ? "+" : ""}${Number(value).toFixed(2)}%`;
}

export default function HoldingsTable({ holdings, onDelete }) {
  if (holdings.length === 0) {
    return <div className="empty-state">No holdings yet. Add one below.</div>;
  }

  return (
    <table>
      <thead>
        <tr>
          <th>Ticker</th>
          <th>Qty</th>
          <th>Buy Price</th>
          <th>Current Price</th>
          <th>Market Value</th>
          <th>Gain/Loss</th>
          {onDelete && <th></th>}
        </tr>
      </thead>
      <tbody>
        {holdings.map((h) => {
          const gainLossPositive = h.gain_loss !== null && Number(h.gain_loss) >= 0;
          return (
            <tr key={h.id}>
              <td>
                <strong>{h.ticker}</strong>
              </td>
              <td>{Number(h.quantity)}</td>
              <td>{formatCurrency(h.buy_price)}</td>
              <td>{formatCurrency(h.current_price)}</td>
              <td>{formatCurrency(h.market_value)}</td>
              <td className={h.gain_loss === null ? "" : gainLossPositive ? "up" : "down"}>
                {formatCurrency(h.gain_loss)} ({formatPct(h.gain_loss_pct)})
              </td>
              {onDelete && (
                <td>
                  <button className="btn-secondary" onClick={() => onDelete(h.id)}>
                    Remove
                  </button>
                </td>
              )}
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}
