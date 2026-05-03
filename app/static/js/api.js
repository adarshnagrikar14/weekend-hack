async function jsonFetch(url, options = {}) {
  const token = localStorage.getItem("orchestrateai_token");
  const authHeader = token ? { Authorization: `Bearer ${token}` } : {};
  const response = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
      ...authHeader,
      ...(options.headers || {}),
    },
    ...options,
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    if (response.status === 401) {
      localStorage.removeItem("orchestrateai_token");
      window.dispatchEvent(new CustomEvent("auth:expired"));
    }
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

export function registerUser(payload) {
  return jsonFetch("/api/auth/register", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function loginUser(payload) {
  return jsonFetch("/api/auth/login", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function logoutUser() {
  return jsonFetch("/api/auth/logout", { method: "POST" });
}

export function getCurrentUser() {
  return jsonFetch("/api/auth/me");
}

export function getUserHistory() {
  return jsonFetch("/api/auth/history");
}

export function getAuthStats() {
  return jsonFetch("/api/auth/stats");
}
