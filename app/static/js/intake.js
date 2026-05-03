import { createDemand, getSamples, runPipeline } from "./api.js";
import { getState, setState } from "./state.js";
import { renderPipeline } from "./pipeline.js";
import { escapeHtml } from "./format.js";
import { goToPage } from "./router.js";

const form = document.querySelector("#intakeForm");
const sampleList = document.querySelector("#sampleList");
const runButton = document.querySelector("#runPipelineBtn");
const loadFirstSampleButton = document.querySelector("#loadFirstSampleBtn");
const demandStatus = document.querySelector("#demandStatus");
const engineBadge = document.querySelector("#engineBadge");

export async function initIntake() {
  const samples = await getSamples();
  setState({ samples });
  sampleList.innerHTML = samples.map(sampleButton).join("");
  sampleList.addEventListener("click", handleSampleClick);
  form.addEventListener("submit", handleSubmit);
  runButton.addEventListener("click", handleRunPipeline);
  loadFirstSampleButton.addEventListener("click", loadFirstSample);

  const geminiEnabled = document.body.dataset.geminiEnabled === "true";
  engineBadge.textContent = geminiEnabled ? "AI assist ready" : "Demo logic ready";
}

function sampleButton(sample, index) {
  const icons = [chatIcon(), peopleIcon(), documentIcon()];
  return `
    <button class="sample-button" type="button" data-sample-index="${index}">
      <span class="sample-icon" aria-hidden="true">${icons[index % icons.length]}</span>
      <span>
        <strong>${escapeHtml(sample.title)}</strong>
        <span>${escapeHtml(sample.business_unit)} - ${escapeHtml(sample.target_date)}</span>
      </span>
    </button>
  `;
}

function loadFirstSample() {
  const [sample] = getState().samples || [];
  if (sample) loadSample(sample);
}

function handleSampleClick(event) {
  const button = event.target.closest("[data-sample-index]");
  if (!button) return;
  const sample = getState().samples[Number(button.dataset.sampleIndex)];
  loadSample(sample);
}

function loadSample(sample) {
  Object.entries(sample).forEach(([key, value]) => {
    const field = form.elements[key];
    if (field) field.value = value;
  });
  demandStatus.textContent = "Sample loaded. Create the demand next.";
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
  demandStatus.textContent = "Preparing triage, routing, assignment, fulfillment, and tracking...";
  try {
    const result = await runPipeline(demandId);
    setState({ pipeline: result });
    renderPipeline(result);
    demandStatus.textContent = "Pipeline ready. Review explainability and rebalance.";
    goToPage("triage");
  } catch (error) {
    demandStatus.textContent = error.message;
  } finally {
    runButton.disabled = false;
    runButton.textContent = "Run AI Pipeline";
  }
}

function chatIcon() {
  return `<svg viewBox="0 0 24 24"><path d="M5 6.5A3.5 3.5 0 018.5 3h7A3.5 3.5 0 0119 6.5v4A3.5 3.5 0 0115.5 14H11l-5 4v-4.2a3.5 3.5 0 01-1-2.4v-4.9z" /></svg>`;
}

function peopleIcon() {
  return `<svg viewBox="0 0 24 24"><path d="M8 11a3 3 0 100-6 3 3 0 000 6zM16 11a3 3 0 100-6 3 3 0 000 6z" /><path d="M3.5 19c.6-3 2.2-4.5 4.5-4.5s3.9 1.5 4.5 4.5M11.5 19c.6-3 2.2-4.5 4.5-4.5s3.9 1.5 4.5 4.5" /></svg>`;
}

function documentIcon() {
  return `<svg viewBox="0 0 24 24"><path d="M7 3h7l4 4v14H7V3z" /><path d="M14 3v5h4M10 12h5M10 16h5" /></svg>`;
}
