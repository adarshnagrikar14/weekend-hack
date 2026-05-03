export function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

export function percent(value) {
  const number = Number(value || 0);
  return `${Math.round(number * 100)}%`;
}

export function chips(items = [], variant = "") {
  return `<div class="chip-row">${items
    .map((item) => `<span class="chip ${variant}">${escapeHtml(item)}</span>`)
    .join("")}</div>`;
}

export function scoreRows(scores = {}) {
  return Object.entries(scores)
    .map(
      ([label, value]) => `
        <div class="score-row">
          <strong>${escapeHtml(label.replaceAll("_", " "))}</strong>
          <span>${escapeHtml(value)}</span>
        </div>
      `
    )
    .join("");
}
