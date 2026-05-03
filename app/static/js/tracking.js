import { escapeHtml, titleLabel } from "./format.js";

const trackingPanel = document.querySelector("#trackingPanel");
const notificationsPanel = document.querySelector("#notificationsPanel");
const evidencePanel = document.querySelector("#evidencePanel");

export function renderTracking(result) {
  if (result.tracking_plan) {
    renderTimeline(result.tracking_plan);
    renderEvidence(result.tracking_plan.automation_evidence || []);
  }
  if (result.notifications) {
    renderNotifications(result.notifications);
  }
}

function renderTimeline(plan) {
  trackingPanel.innerHTML = `
    <div class="panel-title-row">
      <h2>Timeline and SLA Risk</h2>
      <span class="chip warn">${escapeHtml(plan.sla_risk)} risk</span>
    </div>
    <div class="tracking-summary">
      <div><strong>Bottleneck</strong><span>${escapeHtml(plan.bottleneck)}</span></div>
      <div><strong>Next best action</strong><span>${escapeHtml(plan.next_best_action)}</span></div>
    </div>
    <div class="timeline-list">
      ${(plan.timeline || []).map(timelineItem).join("")}
    </div>
  `;
}

function timelineItem(item) {
  return `
    <div class="timeline-item">
      <span class="chip ${item.status === "complete" ? "" : "warn"}">${escapeHtml(titleLabel(item.status))}</span>
      <div>
        <strong>${escapeHtml(item.stage)}</strong>
        <p class="muted">${escapeHtml(item.manual_step_removed)}</p>
      </div>
      <span class="muted">${escapeHtml(item.due_date)}</span>
    </div>
  `;
}

function renderNotifications(notifications) {
  const items = [
    notifications.manager_assignment,
    notifications.resource_request,
    notifications.demand_owner_update,
  ].filter(Boolean);
  notificationsPanel.innerHTML = `
    <div class="panel-title-row">
      <h2>Notification Drafts</h2>
      <span class="chip warn">${formatSendStatus(notifications.send_status)}</span>
    </div>
    <div class="notification-list">
      ${items
        .map(
          (item) => `
            <div class="notification-item">
              <strong>${escapeHtml(item.subject)}</strong>
              <p>To: ${escapeHtml(item.to)}</p>
              <p>${escapeHtml(item.body)}</p>
            </div>
          `
        )
        .join("")}
    </div>
  `;
}

function formatSendStatus(value) {
  if (value === "drafted_not_sent") return "Drafted, not sent";
  return escapeHtml(String(value || "Drafted"));
}

function renderEvidence(evidence) {
  const totalSteps = evidence.reduce((sum, item) => sum + Number(item.manual_steps_removed || 0), 0);
  const totalMinutes = evidence.reduce((sum, item) => sum + Number(item.estimated_minutes_saved || 0), 0);
  evidencePanel.innerHTML = `
    <div class="panel-title-row">
      <h2>Before vs After</h2>
      <span class="score-pill">${totalSteps} steps removed</span>
    </div>
    <p class="evidence-total">${totalMinutes} minutes saved across assignment, routing, staffing, and communication.</p>
    <div class="evidence-list">
      ${evidence
        .map(
          (item) => `
            <div class="evidence-item">
              <div><strong>Before</strong><span>${escapeHtml(item.before)}</span></div>
              <div><strong>After</strong><span>${escapeHtml(item.after)}</span></div>
            </div>
          `
        )
        .join("")}
    </div>
  `;
}
