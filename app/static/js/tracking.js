import { escapeHtml } from "./format.js";

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
    <p class="eyebrow">Track 4</p>
    <h2>Timeline and SLA risk</h2>
    <div class="metric-row">
      <strong>${escapeHtml(plan.sla_risk)} risk</strong>
      <span>${escapeHtml(plan.bottleneck)} Next: ${escapeHtml(plan.next_best_action)}</span>
    </div>
    <div class="timeline">
      ${(plan.timeline || []).map(timelineItem).join("")}
    </div>
  `;
}

function timelineItem(item) {
  return `
    <div class="timeline-item">
      <span class="chip ${item.status === "complete" ? "" : "warn"}">${escapeHtml(item.status)}</span>
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
    <p class="eyebrow">Comms automation</p>
    <h2>Notification drafts</h2>
    <span class="chip warn">${escapeHtml(notifications.send_status)}</span>
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

function renderEvidence(evidence) {
  const totalSteps = evidence.reduce((sum, item) => sum + Number(item.manual_steps_removed || 0), 0);
  const totalMinutes = evidence.reduce((sum, item) => sum + Number(item.estimated_minutes_saved || 0), 0);
  evidencePanel.innerHTML = `
    <p class="eyebrow">Automation evidence</p>
    <h2>${totalSteps} manual steps removed, ${totalMinutes} minutes saved</h2>
    <div class="metric-list">
      ${evidence
        .map(
          (item) => `
            <div class="metric-row">
              <strong>Before: ${escapeHtml(item.before)}</strong>
              <span>After: ${escapeHtml(item.after)}</span>
            </div>
          `
        )
        .join("")}
    </div>
  `;
}
