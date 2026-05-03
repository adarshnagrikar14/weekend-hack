import { explainDecision } from "./api.js";
import { getState } from "./state.js";
import { escapeHtml } from "./format.js";

const answerBox = document.querySelector("#explainAnswer");

export function initVoiceExplainability() {
  document.addEventListener("submit", (event) => {
    if (event.target.matches("[data-explain-form]")) {
      handleExplain(event);
    }
  });
}

async function handleExplain(event) {
  event.preventDefault();
  const { demandId } = getState();
  const targetId = event.target.dataset.answerTarget;
  const targetBox = targetId ? document.querySelector(`#${targetId}`) : answerBox;
  const question = new FormData(event.target).get("question") || "Why this decision?";
  if (!demandId) {
    targetBox.textContent = "Create and run a demand first.";
    return;
  }
  targetBox.textContent = "Preparing explanation...";
  try {
    const result = await explainDecision(demandId, String(question));
    targetBox.innerHTML = `
      <strong>Explanation</strong>
      <p>${escapeHtml(result.answer)}</p>
    `;
  } catch (error) {
    targetBox.textContent = error.message;
  }
}
