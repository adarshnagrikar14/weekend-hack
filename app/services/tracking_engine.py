from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any


def build_tracking_plan(
    demand: dict[str, Any],
    analysis: dict[str, Any],
    decision: dict[str, Any],
    team_plan: dict[str, Any],
) -> dict[str, Any]:
    start = datetime.now(timezone.utc).date()
    stage_days = _stage_days(analysis, decision, team_plan)
    cursor = start
    timeline = []
    for stage, days in stage_days:
        due = cursor + timedelta(days=days)
        timeline.append(
            {
                "stage": stage,
                "status": "complete" if stage in {"Intake", "Triage", "Decision", "Assignment"} else "planned",
                "owner": _owner_for_stage(stage),
                "due_date": due.isoformat(),
                "manual_step_removed": _manual_step_removed(stage),
            }
        )
        cursor = due

    risk = _risk(analysis, decision, team_plan)
    return {
        "timeline": timeline,
        "predicted_completion": cursor.isoformat(),
        "sla_risk": risk["level"],
        "bottleneck": risk["bottleneck"],
        "next_best_action": risk["next_action"],
        "automation_evidence": automation_evidence(),
    }


def automation_evidence() -> list[dict[str, Any]]:
    return [
        {
            "before": "Coordinator reads free-text demand and manually fills triage sheet.",
            "after": "Gemini schema extraction produces domain, priority, complexity, and skills.",
            "manual_steps_removed": 4,
            "estimated_minutes_saved": 35,
        },
        {
            "before": "Managers debate Project vs POC vs Partner path in meetings.",
            "after": "Decision engine scores routes and shows explainable reason chips.",
            "manual_steps_removed": 3,
            "estimated_minutes_saved": 45,
        },
        {
            "before": "Resourcing lead searches spreadsheets for available talent.",
            "after": "Matching engine ranks people by skill, availability, cost, and role fit.",
            "manual_steps_removed": 5,
            "estimated_minutes_saved": 80,
        },
        {
            "before": "Dropouts trigger ad hoc calls and replanning.",
            "after": "Rebalance reruns constraints and proposes replacement with impact.",
            "manual_steps_removed": 3,
            "estimated_minutes_saved": 40,
        },
        {
            "before": "Status emails and audit notes are written manually.",
            "after": "System drafts notifications and logs every stage to SQLite.",
            "manual_steps_removed": 4,
            "estimated_minutes_saved": 30,
        },
    ]


def _stage_days(
    analysis: dict[str, Any], decision: dict[str, Any], team_plan: dict[str, Any]
) -> list[tuple[str, int]]:
    complexity = analysis.get("complexity", "Medium")
    route = decision.get("route", "POC")
    delivery_days = {"Low": 10, "Medium": 21, "High": 42}.get(complexity, 21)
    if route == "Hackathon":
        delivery_days = min(delivery_days, 7)
    if route == "Partner":
        delivery_days += 10
    if team_plan.get("gaps"):
        delivery_days += 7
    return [
        ("Intake", 0),
        ("Triage", 1),
        ("Decision", 1),
        ("Assignment", 2),
        ("Fulfilment", 3),
        ("Kickoff", 2),
        ("Delivery Tracking", delivery_days),
    ]


def _risk(
    analysis: dict[str, Any], decision: dict[str, Any], team_plan: dict[str, Any]
) -> dict[str, str]:
    if team_plan.get("gaps"):
        return {
            "level": "High",
            "bottleneck": f"Open role gap: {', '.join(team_plan['gaps'])}",
            "next_action": "Escalate gap to partner/crowd pool or approve scope reduction.",
        }
    if decision.get("route") == "Partner":
        return {
            "level": "Medium",
            "bottleneck": "Partner due diligence and commercial guardrails",
            "next_action": "Start partner governance checklist in parallel with kickoff.",
        }
    if analysis.get("priority") in {"High", "Critical"}:
        return {
            "level": "Medium",
            "bottleneck": "Fast target date with governance checks",
            "next_action": "Book decision owner and manager review within 24 hours.",
        }
    return {
        "level": "Low",
        "bottleneck": "No major bottleneck predicted",
        "next_action": "Proceed to kickoff with suggested team and assets.",
    }


def _owner_for_stage(stage: str) -> str:
    return {
        "Intake": "Demand owner",
        "Triage": "Intake agent",
        "Decision": "Governance engine",
        "Assignment": "AI Club coordinator",
        "Fulfilment": "Resourcing agent",
        "Kickoff": "Recommended manager",
        "Delivery Tracking": "Tracking agent",
    }[stage]


def _manual_step_removed(stage: str) -> str:
    return {
        "Intake": "No duplicate intake spreadsheet entry",
        "Triage": "No manual skill and domain classification",
        "Decision": "No committee-only route selection",
        "Assignment": "No manual manager shortlist search",
        "Fulfilment": "No spreadsheet-based resource matching",
        "Kickoff": "No manual kickoff summary drafting",
        "Delivery Tracking": "No manual SLA tracker creation",
    }[stage]
