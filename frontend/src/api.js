export const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function request(path, options = {}) {
  const res = await fetch(`${API_URL}${path}`, {
    headers: { "Content-Type": "application/json", ...options.headers },
    ...options,
  });

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      if (body?.detail) {
        detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
      }
    } catch {
      // response wasn't JSON — fall back to statusText
    }
    throw new Error(detail);
  }

  if (res.status === 204) return null;
  return res.json();
}

export const api = {
  getHoldings: () => request("/holdings"),
  createHolding: (data) => request("/holdings", { method: "POST", body: JSON.stringify(data) }),
  deleteHolding: (id) => request(`/holdings/${id}`, { method: "DELETE" }),
  getSummary: () => request("/portfolio/summary"),
  getHistory: () => request("/portfolio/history"),
  triggerAnalysis: () => request("/agent/analyze", { method: "POST" }),
  getRun: (id) => request(`/agent/runs/${id}`),
};
