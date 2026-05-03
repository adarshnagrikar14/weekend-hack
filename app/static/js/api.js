async function jsonFetch(url, options = {}) {
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.detail || "Request failed");
  }
  return payload;
}

export function getSamples() {
  return jsonFetch("/api/samples");
}

export function createDemand(payload) {
  return jsonFetch("/api/demands", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function runPipeline(demandId) {
  return jsonFetch(`/api/demands/${demandId}/run`, { method: "POST" });
}

export function rebalanceDemand(demandId, removedResourceId, reason) {
  return jsonFetch(`/api/demands/${demandId}/rebalance`, {
    method: "POST",
    body: JSON.stringify({
      removed_resource_id: removedResourceId,
      reason,
    }),
  });
}

export function explainDecision(demandId, question) {
  return jsonFetch("/api/voice/explain", {
    method: "POST",
    body: JSON.stringify({ demand_id: demandId, question }),
  });
}
