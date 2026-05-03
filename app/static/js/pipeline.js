import { chips, escapeHtml, percent, scoreRows, titleLabel } from "./format.js";
import { renderTeam } from "./matching.js";
import { renderTracking } from "./tracking.js";

const stageContainer = document.querySelector("#pipelineStages");
const pipelineStrip = document.querySelector("#pipelineStrip");
const demandSnapshotPanel = document.querySelector("#demandSnapshotPanel");
const analysisPanel = document.querySelector("#analysisPanel");
const decisionPanel = document.querySelector("#decisionPanel");
const managerPanel = document.querySelector("#managerPanel");
const routeWhyPanel = document.querySelector("#routeWhyPanel");
const auditPanel = document.querySelector("#auditPanel");
const triageDemandBadge = document.querySelector("#triageDemandBadge");
const fulfillmentRouteBadge = document.querySelector("#fulfillmentRouteBadge");
const fulfillmentRiskBadge = document.querySelector("#fulfillmentRiskBadge");
const trackingRiskBadge = document.querySelector("#trackingRiskBadge");

const stageNames = [
  { key: "Intake", label: "Intake complete" },
  { key: "Triage", label: "Triage complete" },
  { key: "Decision", label: "Routing selected" },
  { key: "Assignment", label: "Assignment pending" },
];

export function renderPipeline(result) {
  renderPageBadges(result);
  renderStages(result);
  renderDemandSnapshot(result.demand);
  renderAnalysis(result.analysis);
  renderDecision(result.decision);
  renderManager(result.manager_assignment);
  renderTeam(result);
  renderTracking(result);
  renderAudit(result.audit || []);
}

function renderPageBadges(result) {
  if (triageDemandBadge) {
    triageDemandBadge.textContent = result.demand?.id ? `Demand #${result.demand.id}` : "No demand selected";
  }
  if (fulfillmentRouteBadge) {
    fulfillmentRouteBadge.textContent = result.decision?.route ? `Route: ${result.decision.route}` : "Route pending";
  }
  const risk = result.tracking_plan?.sla_risk;
  if (fulfillmentRiskBadge) fulfillmentRiskBadge.textContent = risk ? `SLA risk: ${risk}` : "SLA risk pending";
  if (trackingRiskBadge) trackingRiskBadge.textContent = risk ? `${risk} risk` : "Risk pending";
}

function renderStages(result) {
  pipelineStrip.hidden = false;
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
        <div class="stage ${completed.has(stage.key) ? "complete" : ""}">
          <span class="stage-dot">${completed.has(stage.key) ? "✓" : stageNames.indexOf(stage) + 1}</span>
          <p>${stage.label}</p>
        </div>
      `
    )
    .join("");
}

function renderDemandSnapshot(demand) {
  if (!demand) return;
  demandSnapshotPanel.innerHTML = `
    <h2>Demand Snapshot</h2>
    <div class="snapshot-list">
      <div>
        <strong>Problem summary</strong>
        <p>${escapeHtml(demand.problem_statement)}</p>
      </div>
      <div>
        <strong>Business unit</strong>
        <p>${escapeHtml(demand.business_unit)}</p>
      </div>
      <div>
        <strong>Urgency</strong>
        <span class="chip warn">${escapeHtml(demand.target_date)}</span>
      </div>
      <div>
        <strong>Expected impact</strong>
        <p>${escapeHtml(demand.expected_impact)}</p>
      </div>
    </div>
  `;
}

function renderAnalysis(analysis) {
  if (!analysis) return;
  analysisPanel.innerHTML = `
    <h2>AI Classification</h2>
    <div class="classification-list">
      <div><strong>Domain</strong><span>${escapeHtml(analysis.domain)}</span></div>
      <div><strong>Priority</strong><span class="chip warn">${escapeHtml(analysis.priority)}</span></div>
      <div><strong>Complexity</strong><span class="chip">${escapeHtml(analysis.complexity)}</span></div>
      <div><strong>Required Skills</strong>${chips(analysis.required_skills || [])}</div>
      <div>
        <strong>Confidence</strong>
        <span>${percent(analysis.confidence)}</span>
        <span class="confidence-bar"><span style="width:${percent(analysis.confidence)}"></span></span>
      </div>
    </div>
  `;
}

function renderDecision(decision) {
  if (!decision) return;
  decisionPanel.innerHTML = `
    <h2>Route Decision</h2>
    <div class="route-options">
      ${Object.entries(decision.scores || {})
        .map(([route, score]) => routeOption(route, score, decision.route))
        .join("")}
    </div>
  `;
  routeWhyPanel.innerHTML = `
    <h2>Why this route?</h2>
    <div class="why-grid">
      ${(decision.reason_chips || []).slice(0, 4).map((reason) => `<p><span>✓</span>${escapeHtml(reason)}</p>`).join("")}
    </div>
    <form class="ask-form compact-ask" data-explain-form data-answer-target="routeWhyAnswer">
      <input name="question" placeholder="Ask why" />
      <button type="submit" class="icon-action" aria-label="Ask why">↗</button>
    </form>
    <div id="routeWhyAnswer" class="answer-box compact-answer">Ask a follow-up about the decision.</div>
  `;
}

function routeOption(route, score, selectedRoute) {
  const descriptions = {
    Project: "Best fit for production-oriented delivery with measurable business value.",
    POC: "Best for validating feasibility with limited scope and time.",
    Hackathon: "Best for rapid ideation and prototype exploration.",
    Partner: "Best for leveraging external expertise or co-investment.",
  };
  return `
    <div class="route-option ${route === selectedRoute ? "selected" : ""}">
      <span class="radio-dot"></span>
      <div>
        <strong>${escapeHtml(route)}</strong>
        <p>${escapeHtml(descriptions[route] || `Score ${score}`)}</p>
      </div>
    </div>
  `;
}

function renderManager(assignment) {
  if (!assignment) return;
  const manager = assignment.recommended_manager;
  const initials = manager.name
    .split(" ")
    .map((part) => part[0])
    .join("")
    .slice(0, 2);
  managerPanel.innerHTML = `
    <h2>Manager Recommendation</h2>
    <div class="manager-card">
      <span class="avatar">${escapeHtml(initials)}</span>
      <div>
        <strong>${escapeHtml(manager.name)}</strong>
        <p>Match score</p>
      </div>
      <span class="score-pill">${escapeHtml(manager.score)}%</span>
    </div>
    <div class="manager-detail">
      <strong>Expertise</strong>
      <span>${escapeHtml(manager.skills.slice(0, 3).join(", "))}</span>
      <strong>Current load</strong>
      <span>${escapeHtml(manager.current_load)}%</span>
      <strong>Rationale</strong>
      <span>${escapeHtml(manager.why)}</span>
    </div>
  `;
}

function renderAudit(events) {
  auditPanel.innerHTML = events.length
    ? events
        .map(
          (event) => `
            <div class="audit-item">
              <strong>${escapeHtml(titleLabel(event.stage))}</strong>
              <span>${escapeHtml(event.summary)}</span>
            </div>
          `
        )
        .join("")
    : '<div class="empty-state">Audit events will appear after intake.</div>';
}
