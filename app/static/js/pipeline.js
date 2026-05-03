import { chips, escapeHtml, percent, scoreRows } from "./format.js";
import { renderTeam } from "./matching.js";
import { renderTracking } from "./tracking.js";

const stageContainer = document.querySelector("#pipelineStages");
const analysisPanel = document.querySelector("#analysisPanel");
const decisionPanel = document.querySelector("#decisionPanel");
const managerPanel = document.querySelector("#managerPanel");
const auditPanel = document.querySelector("#auditPanel");

const stageNames = [
  "Intake",
  "Triage",
  "Decision",
  "Assignment",
  "Fulfilment",
  "Tracking",
  "Comms",
];

export function renderPipeline(result) {
  renderStages(result);
  renderAnalysis(result.analysis);
  renderDecision(result.decision);
  renderManager(result.manager_assignment);
  renderTeam(result);
  renderTracking(result);
  renderAudit(result.audit || []);
}

function renderStages(result) {
  const completed = new Set(["Intake"]);
  if (result.analysis) completed.add("Triage");
  if (result.decision) completed.add("Decision");
  if (result.manager_assignment) completed.add("Assignment");
  if (result.team_plan) completed.add("Fulfilment");
  if (result.tracking_plan) completed.add("Tracking");
  if (result.notifications) completed.add("Comms");

  stageContainer.innerHTML = stageNames
    .map(
      (stage) => `
        <div class="stage ${completed.has(stage) ? "complete" : ""}">
          <strong>${stage}</strong>
          <p>${completed.has(stage) ? "Automated" : "Waiting"}</p>
        </div>
      `
    )
    .join("");
}

function renderAnalysis(analysis) {
  if (!analysis) return;
  analysisPanel.innerHTML = `
    <p class="eyebrow">Track 1</p>
    <h2>AI triage</h2>
    <div class="stat-grid">
      <div class="metric-row"><strong>Domain</strong><span>${escapeHtml(analysis.domain)}</span></div>
      <div class="metric-row"><strong>Priority</strong><span>${escapeHtml(analysis.priority)}</span></div>
      <div class="metric-row"><strong>Complexity</strong><span>${escapeHtml(analysis.complexity)}</span></div>
      <div class="metric-row"><strong>Confidence</strong><span>${percent(analysis.confidence)}</span></div>
    </div>
    ${chips(analysis.required_skills || [])}
    <div class="metric-row">
      <strong>Summary</strong>
      <span>${escapeHtml(analysis.summary)}</span>
    </div>
    <div class="metric-row">
      <strong>Engine</strong>
      <span>${escapeHtml(analysis.engine || "pipeline")}</span>
    </div>
  `;
}

function renderDecision(decision) {
  if (!decision) return;
  decisionPanel.innerHTML = `
    <p class="eyebrow">Track 2</p>
    <h2>${escapeHtml(decision.route)} route</h2>
    <div class="metric-row">
      <strong>Decision summary</strong>
      <span>${escapeHtml(decision.decision_summary)}</span>
    </div>
    ${chips(decision.reason_chips || [])}
    <div class="stat-grid">${scoreRows(decision.scores)}</div>
    <div class="metric-row">
      <strong>Governance touchpoints</strong>
      <span>${escapeHtml((decision.governance || []).join(" | "))}</span>
    </div>
  `;
}

function renderManager(assignment) {
  if (!assignment) return;
  const manager = assignment.recommended_manager;
  managerPanel.innerHTML = `
    <p class="eyebrow">Assignment</p>
    <h2>${escapeHtml(manager.name)}</h2>
    <div class="metric-row">
      <strong>${escapeHtml(manager.title)}</strong>
      <span>${escapeHtml(manager.why)}</span>
    </div>
    <div class="stat-grid">${scoreRows(manager.score_breakdown)}</div>
    <div class="metric-row">
      <strong>Alternates</strong>
      <span>${escapeHtml((assignment.alternates || []).map((item) => item.name).join(", "))}</span>
    </div>
  `;
}

function renderAudit(events) {
  auditPanel.innerHTML = events.length
    ? events
        .map(
          (event) => `
            <div class="audit-item">
              <strong>${escapeHtml(event.stage)}</strong>
              <span>${escapeHtml(event.summary)}</span>
            </div>
          `
        )
        .join("")
    : '<div class="empty-state">Audit events will appear after intake.</div>';
}
