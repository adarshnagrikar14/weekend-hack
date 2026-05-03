import { explainDecision } from "./api.js";
import { getState } from "./state.js";
import { escapeHtml } from "./format.js";

const form = document.querySelector("#explainForm");
const answerBox = document.querySelector("#explainAnswer");

export function initVoiceExplainability() {
  form.addEventListener("submit", handleExplain);
}

async function handleExplain(event) {
  event.preventDefault();
  const { demandId } = getState();
  const question = new FormData(form).get("question") || "Why this decision?";
  if (!demandId) {
    answerBox.textContent = "Create and run a demand first.";
    return;
  }
  answerBox.textContent = "Generating grounded explanation...";
  try {
    const result = await explainDecision(demandId, String(question));
    answerBox.innerHTML = `
      <strong>${escapeHtml(result.mode)}</strong>
      <p>${escapeHtml(result.answer)}</p>
      <p class="muted">${escapeHtml(result.voice_ready)}</p>
    `;
  } catch (error) {
    answerBox.textContent = error.message;
  }
}
