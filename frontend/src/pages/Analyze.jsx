import { useEffect, useRef, useState } from "react";
import { api, API_URL } from "../api";

const POLL_INTERVAL_MS = 2500;

export default function Analyze() {
  const [run, setRun] = useState(null);
  const [error, setError] = useState(null);
  const [starting, setStarting] = useState(false);
  const pollRef = useRef(null);

  useEffect(() => () => clearInterval(pollRef.current), []);

  function pollRun(runId) {
    clearInterval(pollRef.current);
    pollRef.current = setInterval(async () => {
      try {
        const updated = await api.getRun(runId);
        setRun(updated);
        if (updated.status !== "running") {
          clearInterval(pollRef.current);
        }
      } catch (err) {
        setError(err.message);
        clearInterval(pollRef.current);
      }
    }, POLL_INTERVAL_MS);
  }

  async function handleAnalyze() {
    setError(null);
    setStarting(true);
    try {
      const started = await api.triggerAnalysis();
      setRun(started);
      pollRun(started.id);
    } catch (err) {
      setError(err.message);
    } finally {
      setStarting(false);
    }
  }

  return (
    <div className="page">
      <h1>Portfolio Analyst</h1>

      <div className="card">
        <p className="muted" style={{ marginTop: 0 }}>
          Reviews your allocation, checks recent news on your top holdings, and produces a
          risk/diversification summary — exported as Excel and PowerPoint.
        </p>
        <button className="btn" onClick={handleAnalyze} disabled={starting || run?.status === "running"}>
          {run?.status === "running" ? "Analyzing…" : "Run Analysis"}
        </button>
      </div>

      {error && <div className="error-banner">{error}</div>}

      {run && (
        <div className="card">
          <h2>
            Run #{run.id} <span className={`run-status ${run.status}`}>{run.status}</span>
          </h2>

          {run.status === "running" && (
            <p className="muted">
              The agent is reviewing your allocation and checking news on your top holdings —
              this usually takes 10–20 seconds.
            </p>
          )}

          {run.status === "failed" && <div className="error-banner">{run.summary}</div>}

          {run.status === "success" && (
            <>
              <p>{run.summary}</p>
              <div className="download-links">
                {run.excel_url && (
                  <a href={`${API_URL}${run.excel_url}`}>📊 Download Excel</a>
                )}
                {run.pptx_url && (
                  <a href={`${API_URL}${run.pptx_url}`}>📑 Download PowerPoint</a>
                )}
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}
