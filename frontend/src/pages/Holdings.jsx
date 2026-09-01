import { useEffect, useState } from "react";
import { api } from "../api";
import HoldingsTable from "../components/HoldingsTable";

const EMPTY_FORM = { ticker: "", quantity: "", buy_price: "" };

export default function Holdings() {
  const [holdings, setHoldings] = useState(null);
  const [form, setForm] = useState(EMPTY_FORM);
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  function load() {
    api
      .getHoldings()
      .then(setHoldings)
      .catch((err) => setError(err.message));
  }

  useEffect(load, []);

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await api.createHolding({
        ticker: form.ticker,
        quantity: Number(form.quantity),
        buy_price: Number(form.buy_price),
      });
      setForm(EMPTY_FORM);
      load();
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDelete(id) {
    setError(null);
    try {
      await api.deleteHolding(id);
      load();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="page">
      <h1>Holdings</h1>

      {error && <div className="error-banner">{error}</div>}

      <div className="card">
        <h2>Add a holding</h2>
        <form onSubmit={handleSubmit}>
          <div className="form-row">
            <div className="form-field">
              <label htmlFor="ticker">Ticker</label>
              <input
                id="ticker"
                required
                placeholder="AAPL"
                value={form.ticker}
                onChange={(e) => setForm({ ...form, ticker: e.target.value })}
              />
            </div>
            <div className="form-field">
              <label htmlFor="quantity">Quantity</label>
              <input
                id="quantity"
                required
                type="number"
                step="any"
                min="0"
                placeholder="10"
                value={form.quantity}
                onChange={(e) => setForm({ ...form, quantity: e.target.value })}
              />
            </div>
            <div className="form-field">
              <label htmlFor="buy_price">Buy Price</label>
              <input
                id="buy_price"
                required
                type="number"
                step="any"
                min="0"
                placeholder="150.00"
                value={form.buy_price}
                onChange={(e) => setForm({ ...form, buy_price: e.target.value })}
              />
            </div>
            <button className="btn" type="submit" disabled={submitting}>
              {submitting ? "Adding…" : "Add Holding"}
            </button>
          </div>
        </form>
      </div>

      <div className="card">
        <h2>Your holdings</h2>
        {holdings === null ? (
          <div className="empty-state">Loading…</div>
        ) : (
          <HoldingsTable holdings={holdings} onDelete={handleDelete} />
        )}
      </div>
    </div>
  );
}
