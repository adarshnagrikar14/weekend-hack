import { rebalanceDemand } from "./api.js";
import { escapeHtml } from "./format.js";
import { getState, setState } from "./state.js";

const teamPanel = document.querySelector("#teamPanel");
const assetPanel = document.querySelector("#assetPanel");
const rebalancePanel = document.querySelector("#rebalancePanel");

export function renderTeam(result) {
  const teamPlan = result.team_plan;
  if (!teamPlan) return;

  teamPanel.innerHTML = `
    <div class="panel-title-row">
      <h2>Recommended Team</h2>
      <span class="score-pill">${escapeHtml(teamPlan.coverage_score)}% coverage</span>
    </div>
    <div class="resource-table">
      <div class="resource-row resource-head">
        <span>Role</span>
        <span>Person</span>
        <span>Skill fit</span>
        <span>Availability</span>
        <span>Workload</span>
        <span>Action</span>
      </div>
      ${(teamPlan.team || []).map(teamMember).join("")}
    </div>
  `;
  teamPanel.querySelectorAll("[data-rebalance-id]").forEach((button) => {
    button.addEventListener("click", handleRebalance);
  });

  assetPanel.innerHTML = `
    <h2>Reusable Assets</h2>
    <div class="asset-table">
      <div class="asset-row asset-head">
        <span>Asset</span>
        <span>Fit reason</span>
        <span>Estimated effort saved</span>
      </div>
      ${(teamPlan.assets || []).map(assetItem).join("")}
    </div>
  `;

  renderRebalance(teamPlan);
}

function teamMember(member) {
  if (member.gap) {
    return `
      <div class="resource-row">
        <span>${escapeHtml(member.role)}</span>
        <span>Open gap</span>
        <span class="chip warn">Escalate</span>
        <span>Needs review</span>
        <span>-</span>
        <span>-</span>
      </div>
    `;
  }
  const resource = member.resource;
  const skillFit = Math.min(99, Math.max(72, Number(resource.match_score || 84)));
  const workload = Math.max(35, 100 - Number(resource.availability || 50));
  return `
    <div class="resource-row">
      <span class="role-cell">${personIcon()}${escapeHtml(member.role)}</span>
      <span>${escapeHtml(resource.name)}</span>
      <span><strong class="fit-pill">${skillFit}%</strong></span>
      <span><span class="availability-dot"></span>Available ${resource.availability >= 60 ? "now" : "soon"}</span>
      <span><span class="load-bar"><span style="width:${workload}%"></span></span>${workload}% allocated</span>
      <button class="ghost-action" type="button" data-rebalance-id="${escapeHtml(resource.id)}">
        Mark unavailable
      </button>
    </div>
  `;
}

function assetItem(asset) {
  return `
    <div class="asset-row">
      <span class="role-cell">${assetIcon()}${escapeHtml(asset.name)}</span>
      <span>${escapeHtml(asset.description)}</span>
      <strong>${escapeHtml(asset.saves_days)} days</strong>
    </div>
  `;
}

function renderRebalance(teamPlan) {
  if (!teamPlan.rebalance) {
    rebalancePanel.innerHTML = `
      <h2>Rebalance Simulation</h2>
      <p class="muted">Mark a recommended team member unavailable to simulate replacement.</p>
    `;
    return;
  }

  rebalancePanel.innerHTML = `
    <h2>Rebalance Simulation</h2>
    <p class="muted">If ${escapeHtml(teamPlan.rebalance.removed_resource_name)} becomes unavailable</p>
    <div class="rebalance-card">
      <span>Before</span>
      <strong>${escapeHtml(teamPlan.rebalance.removed_resource_name)}</strong>
    </div>
    <div class="rebalance-arrow">↓</div>
    <div class="rebalance-card selected">
      <span>After</span>
      <strong>${escapeHtml(nextReplacement(teamPlan))}</strong>
    </div>
    <div class="impact-grid">
      <div><strong>Impact</strong><span>${escapeHtml(teamPlan.rebalance.impact)}</span></div>
      <div><strong>Coverage</strong><span>${escapeHtml(teamPlan.coverage_score)}%</span></div>
    </div>
  `;
}

function nextReplacement(teamPlan) {
  const removed = teamPlan.rebalance?.removed_resource_name;
  const replacement = (teamPlan.team || []).find((member) => member.resource && member.resource.name !== removed);
  return replacement?.resource?.name || "Replacement pending";
}

function personIcon() {
  return `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 12a4 4 0 100-8 4 4 0 000 8zM5 21a7 7 0 0114 0" /></svg>`;
}

function assetIcon() {
  return `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 3h7l4 4v14H7V3z" /><path d="M14 3v5h4M10 13h5M10 17h4" /></svg>`;
}

async function handleRebalance(event) {
  const removedResourceId = event.currentTarget.dataset.rebalanceId;
  const { demandId } = getState();
  if (!demandId || !removedResourceId) return;
  event.currentTarget.textContent = "Rebalancing...";
  event.currentTarget.disabled = true;
  try {
    const result = await rebalanceDemand(
      demandId,
      removedResourceId,
      "Demo simulation: resource became unavailable."
    );
    setState({ pipeline: result });
    document.dispatchEvent(new CustomEvent("pipeline:updated", { detail: result }));
  } catch (error) {
    event.currentTarget.textContent = error.message;
  }
}
