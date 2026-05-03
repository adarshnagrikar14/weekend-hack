from __future__ import annotations

from typing import Any


def draft_notifications(
    demand: dict[str, Any],
    analysis: dict[str, Any],
    decision: dict[str, Any],
    manager_assignment: dict[str, Any],
    team_plan: dict[str, Any],
) -> dict[str, Any]:
    manager = manager_assignment["recommended_manager"]
    team_names = [
        member["resource"]["name"]
        for member in team_plan.get("team", [])
        if member.get("resource")
    ]
    assets = [asset["name"] for asset in team_plan.get("assets", [])]
    return {
        "send_status": "drafted_not_sent",
        "manager_assignment": {
            "to": manager["name"],
            "subject": f"Recommended ownership: {demand['title']}",
            "body": (
                f"You are recommended to own '{demand['title']}' for {demand['business_unit']}. "
                f"Route: {decision['route']}. Domain: {analysis['domain']}. "
                f"Reason: {decision['decision_summary']} Next step: validate scope and kickoff."
            ),
        },
        "resource_request": {
            "to": "AI Club resourcing desk",
            "subject": f"Resource plan ready: {demand['title']}",
            "body": (
                f"Suggested team: {', '.join(team_names)}. "
                f"Reusable assets: {', '.join(assets)}. "
                f"Fulfillment model: {team_plan['fulfilment_model']}."
            ),
        },
        "demand_owner_update": {
            "to": demand["requester"],
            "subject": f"AI Club pipeline decision: {decision['route']}",
            "body": (
                f"Your demand has completed automated triage. Recommended route is "
                f"{decision['route']} with {round(decision['confidence'] * 100)}% confidence. "
                "The proposed manager, team, assets, and timeline are ready for review."
            ),
        },
    }
