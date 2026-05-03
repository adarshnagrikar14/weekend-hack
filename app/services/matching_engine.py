from __future__ import annotations

from typing import Any

from app.services import data_loader


ROLE_BLUEPRINTS = {
    "Low": ["Business Analyst", "AI Engineer", "Full-stack Engineer"],
    "Medium": ["Business Analyst", "AI Engineer", "Full-stack Engineer", "QA / Governance"],
    "High": [
        "Business Analyst",
        "Solution Architect",
        "AI Engineer",
        "Full-stack Engineer",
        "Data / MLOps Engineer",
        "QA / Governance",
    ],
}


def build_team_plan(
    analysis: dict[str, Any],
    demand: dict[str, Any],
    excluded_resource_ids: set[str] | None = None,
) -> dict[str, Any]:
    excluded = excluded_resource_ids or set()
    required_roles = ROLE_BLUEPRINTS.get(analysis.get("complexity", "Medium"), ROLE_BLUEPRINTS["Medium"])
    resources = [resource for resource in data_loader.resources() if resource["id"] not in excluded]
    ranked_by_role = {
        role: _rank_resources_for_role(role, resources, analysis) for role in required_roles
    }

    selected_ids: set[str] = set()
    team = []
    for role in required_roles:
        candidates = [candidate for candidate in ranked_by_role[role] if candidate["id"] not in selected_ids]
        if not candidates:
            team.append(
                {
                    "role": role,
                    "resource": None,
                    "gap": True,
                    "reason": "No available candidate met hard constraints.",
                }
            )
            continue
        selected = candidates[0]
        selected_ids.add(selected["id"])
        team.append(
            {
                "role": role,
                "resource": selected,
                "gap": False,
                "reason": selected["match_reason"],
            }
        )

    gaps = [member["role"] for member in team if member["gap"]]
    assets = recommend_assets(analysis)
    return {
        "team": team,
        "assets": assets,
        "gaps": gaps,
        "coverage_score": _coverage_score(team),
        "fulfilment_model": _fulfilment_model(analysis, assets, gaps),
        "explainability": [
            "Hard constraints remove unavailable or overloaded resources.",
            "Weighted fit ranks skill overlap, role match, availability, and proficiency.",
            "Reusable assets are recommended before net-new staffing expansion.",
        ],
    }


def rebalance_team(
    current_team: dict[str, Any],
    analysis: dict[str, Any],
    demand: dict[str, Any],
    removed_resource_id: str,
    reason: str,
) -> dict[str, Any]:
    excluded = {removed_resource_id}
    for member in current_team.get("team", []):
        resource = member.get("resource")
        if resource and resource.get("id") == removed_resource_id:
            break
    new_plan = build_team_plan(analysis, demand, excluded)
    removed_name = _resource_name(removed_resource_id)
    new_plan["rebalance"] = {
        "removed_resource_id": removed_resource_id,
        "removed_resource_name": removed_name,
        "reason": reason,
        "impact": _rebalance_impact(current_team, new_plan),
        "explanation": (
            f"{removed_name} was excluded, constraints were rerun, and the next best "
            "available candidates were selected with updated coverage and risk."
        ),
    }
    return new_plan


def recommend_assets(analysis: dict[str, Any]) -> list[dict[str, Any]]:
    required_skills = set(analysis.get("required_skills", []))
    domain = analysis.get("domain")
    ranked = []
    for asset in data_loader.assets():
        skill_score = len(required_skills.intersection(asset["skills"])) * 12
        domain_score = 18 if domain in asset["domains"] else 4
        score = asset["reuse_score"] + skill_score + domain_score + asset["saves_days"]
        ranked.append({**asset, "fit_score": score})
    ranked.sort(key=lambda item: item["fit_score"], reverse=True)
    return ranked[:3]


def _rank_resources_for_role(
    role: str, resources: list[dict[str, Any]], analysis: dict[str, Any]
) -> list[dict[str, Any]]:
    required_skills = set(analysis.get("required_skills", []))
    ranked = []
    for resource in resources:
        if resource["availability"] < 35:
            continue
        role_fit = 30 if resource["role"] == role else _adjacent_role_score(role, resource["role"])
        skill_overlap = len(required_skills.intersection(resource["skills"])) * 12
        availability_score = round(resource["availability"] / 4)
        proficiency_score = round(resource["proficiency"] / 5)
        cost_score = {"L": 12, "M": 8, "H": 4}.get(resource["cost_band"], 6)
        score = role_fit + skill_overlap + availability_score + proficiency_score + cost_score
        ranked.append(
            {
                **resource,
                "match_score": score,
                "score_breakdown": {
                    "role_fit": role_fit,
                    "skill_overlap": skill_overlap,
                    "availability": availability_score,
                    "proficiency": proficiency_score,
                    "cost": cost_score,
                },
                "match_reason": (
                    f"{resource['name']} scores {score} for {role}: role fit {role_fit}, "
                    f"skill overlap {skill_overlap}, availability {availability_score}."
                ),
            }
        )
    ranked.sort(key=lambda item: item["match_score"], reverse=True)
    return ranked


def _adjacent_role_score(target_role: str, resource_role: str) -> int:
    adjacent = {
        "AI Engineer": {"Solution Architect", "Data / MLOps Engineer"},
        "Full-stack Engineer": {"Solution Architect"},
        "Data / MLOps Engineer": {"AI Engineer", "Solution Architect"},
        "QA / Governance": {"Business Analyst", "Solution Architect"},
        "Business Analyst": {"QA / Governance", "Solution Architect"},
        "Solution Architect": {"AI Engineer", "Full-stack Engineer"},
    }
    return 15 if resource_role in adjacent.get(target_role, set()) else 4


def _coverage_score(team: list[dict[str, Any]]) -> int:
    if not team:
        return 0
    filled = sum(1 for member in team if not member["gap"])
    return round((filled / len(team)) * 100)


def _fulfilment_model(
    analysis: dict[str, Any], assets: list[dict[str, Any]], gaps: list[str]
) -> str:
    if gaps:
        return "Hybrid team plus partner/crowd support for open gaps"
    if assets and assets[0]["fit_score"] > 105:
        return "Asset-led delivery with small focused team"
    if analysis.get("complexity") == "High":
        return "Managed project squad"
    return "POC squad with reusable accelerators"


def _resource_name(resource_id: str) -> str:
    for resource in data_loader.resources():
        if resource["id"] == resource_id:
            return resource["name"]
    return resource_id


def _rebalance_impact(current_team: dict[str, Any], new_plan: dict[str, Any]) -> str:
    old_score = current_team.get("coverage_score", 0)
    new_score = new_plan.get("coverage_score", 0)
    if new_score >= old_score:
        return "Coverage preserved with no added gap."
    return f"Coverage reduced from {old_score}% to {new_score}%; manager should review risk."
