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
          <strong>${escapeHtml(titleLabel(label))}</strong>
          <span>${escapeHtml(value)}</span>
        </div>
      `
    )
    .join("");
}

export function titleLabel(value) {
  const label = String(value ?? "")
    .replaceAll("_", " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
  return label.replaceAll("Fulfilment", "Fulfillment");
}
