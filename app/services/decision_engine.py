from __future__ import annotations

from typing import Any

from app.services import data_loader


def route_demand(analysis: dict[str, Any], demand: dict[str, Any]) -> dict[str, Any]:
    scores = _route_scores(analysis, demand)
    route = max(scores, key=scores.get)
    reason_chips = _reason_chips(route, analysis, scores)

    return {
        "route": route,
        "confidence": round(scores[route] / max(sum(scores.values()), 1), 2),
        "scores": scores,
        "reason_chips": reason_chips,
        "governance": _governance_steps(route, analysis),
        "decision_summary": (
            f"{route} is recommended because {reason_chips[0].lower()} and "
            f"{reason_chips[1].lower()}."
        ),
    }


def recommend_manager(
    analysis: dict[str, Any], demand: dict[str, Any]
) -> dict[str, Any]:
    ranked = []
    required_skills = set(analysis.get("required_skills", []))
    for manager in data_loader.managers():
        domain_fit = 25 if analysis.get("domain") in manager["domains"] else 8
        bu_fit = 15 if demand.get("business_unit") in manager["business_units"] else 6
        skill_overlap = len(required_skills.intersection(manager["skills"])) * 9
        workload_score = max(0, 25 - round(manager["current_load"] / 4))
        availability_score = 15 if manager["availability"] == "available" else 7
        delivery_score = round(manager["delivery_score"] / 10)
        total = domain_fit + bu_fit + skill_overlap + workload_score + availability_score + delivery_score
        ranked.append(
            {
                **manager,
                "score": total,
                "score_breakdown": {
                    "domain_fit": domain_fit,
                    "business_unit_fit": bu_fit,
                    "skill_overlap": skill_overlap,
                    "workload": workload_score,
                    "availability": availability_score,
                    "delivery_history": delivery_score,
                },
                "why": _manager_why(manager, analysis, total),
            }
        )

    ranked.sort(key=lambda item: item["score"], reverse=True)
    return {
        "recommended_manager": ranked[0],
        "alternates": ranked[1:3],
        "assignment_policy": "Ranked by expertise, BU ownership, skill overlap, workload, availability, and delivery history.",
    }


def _route_scores(analysis: dict[str, Any], demand: dict[str, Any]) -> dict[str, int]:
    text = " ".join(str(value) for value in demand.values()).lower()
    complexity = analysis.get("complexity", "Medium")
    quick_win = bool(analysis.get("quick_win"))
    net_new = bool(analysis.get("net_new_innovation"))
    dependencies = len(analysis.get("dependencies", []))
    required_skills = set(analysis.get("required_skills", []))

    scores = {
        "Project": 45,
        "POC": 42,
        "Hackathon": 36,
        "Partner": 24,
    }
    if quick_win:
        scores["POC"] += 22
        scores["Hackathon"] += 12
    if complexity == "High":
        scores["Project"] += 24
        scores["Partner"] += 10
    if complexity == "Low":
        scores["Hackathon"] += 20
        scores["POC"] += 10
    if net_new:
        scores["POC"] += 12
        scores["Partner"] += 8
    if dependencies >= 3:
        scores["Project"] += 10
    if {"Live API", "Partner Governance"}.intersection(required_skills) or "partner" in text:
        scores["Partner"] += 26
    if "prototype" in text or "pilot" in text:
        scores["POC"] += 18
    if "hackathon" in text or "quick" in text:
        scores["Hackathon"] += 14
    return scores


def _reason_chips(route: str, analysis: dict[str, Any], scores: dict[str, int]) -> list[str]:
    chips = [
        f"{analysis.get('complexity', 'Medium')} complexity",
        f"{analysis.get('priority', 'Medium')} priority",
        f"{analysis.get('domain', 'Workflow Automation')} domain fit",
    ]
    if analysis.get("quick_win"):
        chips.append("Quick-win potential")
    if route == "Partner":
        chips.append("Specialist capability or ecosystem leverage")
    if route == "Project":
        chips.append("Governance and delivery control needed")
    if route == "POC":
        chips.append("Pilotable scope before scale")
    if route == "Hackathon":
        chips.append("Low-risk rapid experimentation fit")
    chips.append(f"Top score {scores[route]}")
    return chips


def _governance_steps(route: str, analysis: dict[str, Any]) -> list[str]:
    steps = ["Confirm dummy data boundary", "Demand owner validates extracted scope"]
    if analysis.get("sensitivity_flag"):
        steps.append("Responsible AI and audit review")
    if route in {"Project", "Partner"}:
        steps.append("Steering approval before kickoff")
    if route == "Partner":
        steps.append("Partner due diligence and commercial guardrails")
    return steps


def _manager_why(manager: dict[str, Any], analysis: dict[str, Any], total: int) -> str:
    return (
        f"{manager['name']} matches {analysis.get('domain', 'the demand')} with "
        f"{manager['current_load']}% current load and a composite score of {total}."
    )
