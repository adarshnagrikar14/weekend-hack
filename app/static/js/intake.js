import { createDemand, getSamples, runPipeline } from "./api.js";
import { getState, setState } from "./state.js";
import { renderPipeline } from "./pipeline.js";
import { escapeHtml } from "./format.js";

const form = document.querySelector("#intakeForm");
const sampleList = document.querySelector("#sampleList");
const runButton = document.querySelector("#runPipelineBtn");
const demandStatus = document.querySelector("#demandStatus");
const engineBadge = document.querySelector("#engineBadge");

export async function initIntake() {
  const samples = await getSamples();
  setState({ samples });
  sampleList.innerHTML = samples.map(sampleButton).join("");
  sampleList.addEventListener("click", handleSampleClick);
  form.addEventListener("submit", handleSubmit);
  runButton.addEventListener("click", handleRunPipeline);

  const geminiEnabled = document.body.dataset.geminiEnabled === "true";
  engineBadge.textContent = geminiEnabled ? "Gemini enabled" : "Fallback engine ready";
}

function sampleButton(sample, index) {
  return `
    <button class="sample-button" type="button" data-sample-index="${index}">
      <strong>${escapeHtml(sample.title)}</strong>
      <span>${escapeHtml(sample.business_unit)} - ${escapeHtml(sample.target_date)}</span>
    </button>
  `;
}

function handleSampleClick(event) {
  const button = event.target.closest("[data-sample-index]");
  if (!button) return;
  const sample = getState().samples[Number(button.dataset.sampleIndex)];
  Object.entries(sample).forEach(([key, value]) => {
    const field = form.elements[key];
    if (field) field.value = value;
  });
  demandStatus.textContent = "Sample loaded. Create the demand record next.";
}

async function handleSubmit(event) {
  event.preventDefault();
  demandStatus.textContent = "Creating demand record...";
  const payload = Object.fromEntries(new FormData(form).entries());
  try {
    const result = await createDemand(payload);
    setState({ demandId: result.demand.id, pipeline: result });
    runButton.disabled = false;
    demandStatus.textContent = `Demand #${result.demand.id} created. Run the pipeline.`;
    renderPipeline(result);
  } catch (error) {
    demandStatus.textContent = error.message;
  }
}

async function handleRunPipeline() {
  const { demandId } = getState();
  if (!demandId) return;
  runButton.disabled = true;
  runButton.textContent = "Running...";
  demandStatus.textContent = "Automating triage, decision, assignment, fulfilment, tracking...";
  try {
    const result = await runPipeline(demandId);
    setState({ pipeline: result });
    renderPipeline(result);
    demandStatus.textContent = "Pipeline ready. Review explainability and rebalance.";
  } catch (error) {
    demandStatus.textContent = error.message;
  } finally {
    runButton.disabled = false;
    runButton.textContent = "Run AI Pipeline";
  }
}
