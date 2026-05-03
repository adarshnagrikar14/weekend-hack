import { rebalanceDemand } from "./api.js";
import { escapeHtml, scoreRows } from "./format.js";
import { getState, setState } from "./state.js";

const teamPanel = document.querySelector("#teamPanel");
const assetPanel = document.querySelector("#assetPanel");

export function renderTeam(result) {
  const teamPlan = result.team_plan;
  if (!teamPlan) return;

  teamPanel.innerHTML = `
    <p class="eyebrow">Track 3</p>
    <h2>Resource fulfilment and rebalance</h2>
    <div class="metric-row">
      <strong>${escapeHtml(teamPlan.fulfilment_model)}</strong>
      <span>Coverage score ${escapeHtml(teamPlan.coverage_score)}%. ${escapeHtml(
        (teamPlan.explainability || [])[0] || ""
      )}</span>
    </div>
    <div class="team-list">
      ${(teamPlan.team || []).map(teamMember).join("")}
    </div>
    ${
      teamPlan.rebalance
        ? `<div class="metric-row"><strong>Rebalance impact</strong><span>${escapeHtml(
            teamPlan.rebalance.explanation
          )}</span></div>`
        : ""
    }
  `;
  teamPanel.querySelectorAll("[data-rebalance-id]").forEach((button) => {
    button.addEventListener("click", handleRebalance);
  });

  assetPanel.innerHTML = `
    <p class="eyebrow">Asset-first</p>
    <h2>Reusable accelerators</h2>
    <div class="asset-list">
      ${(teamPlan.assets || []).map(assetItem).join("")}
    </div>
  `;
}

function teamMember(member) {
  if (member.gap) {
    return `
      <div class="team-member">
        <strong>${escapeHtml(member.role)}</strong>
        <p>Open gap</p>
        <span class="chip warn">Escalate</span>
      </div>
    `;
  }
  const resource = member.resource;
  return `
    <div class="team-member">
      <div>
        <strong>${escapeHtml(member.role)}</strong>
        <p>${escapeHtml(resource.role)}</p>
      </div>
      <div>
        <strong>${escapeHtml(resource.name)}</strong>
        <p>${escapeHtml(member.reason)}</p>
        <div class="stat-grid">${scoreRows(resource.score_breakdown)}</div>
      </div>
      <button class="ghost-action" type="button" data-rebalance-id="${escapeHtml(resource.id)}">
        Mark unavailable
      </button>
    </div>
  `;
}

function assetItem(asset) {
  return `
    <div class="asset-item">
      <strong>${escapeHtml(asset.name)}</strong>
      <p>${escapeHtml(asset.description)}</p>
      <span class="chip">${escapeHtml(asset.type)} - saves ${escapeHtml(asset.saves_days)} days</span>
    </div>
  `;
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
