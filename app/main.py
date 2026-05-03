from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app import db
from app.config import BASE_DIR, settings
from app.schemas import DemandCreate, ExplainRequest, RebalanceRequest
from app.services import data_loader
from app.services.decision_engine import recommend_manager, route_demand
from app.services.gemini_service import analyze_demand, concise_explanation
from app.services.matching_engine import build_team_plan, rebalance_team
from app.services.notification_service import draft_notifications
from app.services.tracking_engine import build_tracking_plan


app = FastAPI(title=settings.app_name)

templates = Jinja2Templates(directory=str(BASE_DIR / "app" / "templates"))
app.mount(
    "/static",
    StaticFiles(directory=str(BASE_DIR / "app" / "static")),
    name="static",
)


@app.on_event("startup")
def startup() -> None:
    db.init_db()


@app.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "app_name": settings.app_name,
            "ngrok_url": settings.ngrok_url,
            "gemini_enabled": settings.gemini_enabled,
        },
    )


@app.get("/api/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "app": settings.app_name,
        "gemini_enabled": settings.gemini_enabled,
        "database": Path(settings.database_path).name,
    }


@app.get("/api/samples")
def samples() -> list[dict[str, Any]]:
    return data_loader.sample_demands()


@app.post("/api/demands")
def create_demand(payload: DemandCreate) -> dict[str, Any]:
    demand = db.insert_demand(payload.model_dump())
    return {"demand": demand, "audit": db.list_audit_events(demand["id"])}


@app.get("/api/demands/{demand_id}")
def get_demand(demand_id: int) -> dict[str, Any]:
    demand = _load_demand_or_404(demand_id)
    return _collect_pipeline_state(demand)


@app.post("/api/demands/{demand_id}/run")
def run_pipeline(demand_id: int) -> dict[str, Any]:
    demand = _load_demand_or_404(demand_id)

    analysis = analyze_demand(demand)
    db.upsert_payload("analyses", demand_id, analysis)
    db.add_audit_event(
        demand_id,
        "triage",
        f"AI triage completed with {analysis['confidence']:.0%} confidence.",
        analysis,
    )

    decision = route_demand(analysis, demand)
    db.upsert_payload("decisions", demand_id, decision)
    db.add_audit_event(
        demand_id,
        "decision",
        f"Route selected: {decision['route']}.",
        decision,
    )

    manager_assignment = recommend_manager(analysis, demand)
    db.upsert_payload("manager_assignments", demand_id, manager_assignment)
    db.add_audit_event(
        demand_id,
        "assignment",
        f"Manager recommended: {manager_assignment['recommended_manager']['name']}.",
        manager_assignment,
    )

    team_plan = build_team_plan(analysis, demand)
    db.upsert_payload("team_plans", demand_id, team_plan)
    db.add_audit_event(
        demand_id,
        "fulfilment",
        f"Team plan created with {team_plan['coverage_score']}% role coverage.",
        team_plan,
    )

    tracking_plan = build_tracking_plan(demand, analysis, decision, team_plan)
    db.upsert_payload("tracking_plans", demand_id, tracking_plan)
    db.add_audit_event(
        demand_id,
        "tracking",
        f"Tracking plan generated with {tracking_plan['sla_risk']} SLA risk.",
        tracking_plan,
    )

    notifications = draft_notifications(
        demand, analysis, decision, manager_assignment, team_plan
    )
    db.upsert_payload("notifications", demand_id, notifications)
    db.add_audit_event(
        demand_id,
        "communications",
        "Manager, resourcing, and demand-owner notification drafts created.",
        notifications,
    )

    db.update_demand_status(demand_id, "pipeline_ready")
    return _collect_pipeline_state(_load_demand_or_404(demand_id))


@app.post("/api/demands/{demand_id}/rebalance")
def rebalance(demand_id: int, payload: RebalanceRequest) -> dict[str, Any]:
    demand = _load_demand_or_404(demand_id)
    analysis = _load_payload_or_404("analyses", demand_id, "Run pipeline first.")
    current_team = _load_payload_or_404("team_plans", demand_id, "Run pipeline first.")
    decision = _load_payload_or_404("decisions", demand_id, "Run pipeline first.")

    new_team = rebalance_team(
        current_team,
        analysis,
        demand,
        payload.removed_resource_id,
        payload.reason,
    )
    db.upsert_payload("team_plans", demand_id, new_team)
    db.add_audit_event(
        demand_id,
        "rebalance",
        new_team["rebalance"]["explanation"],
        new_team,
    )

    tracking_plan = build_tracking_plan(demand, analysis, decision, new_team)
    db.upsert_payload("tracking_plans", demand_id, tracking_plan)
    db.update_demand_status(demand_id, "rebalanced")
    return _collect_pipeline_state(_load_demand_or_404(demand_id))


@app.post("/api/voice/explain")
def explain(payload: ExplainRequest) -> dict[str, str]:
    demand = _load_demand_or_404(payload.demand_id)
    context = _collect_pipeline_state(demand)
    answer = concise_explanation(payload.question, context)
    db.add_audit_event(
        payload.demand_id,
        "voice_explainability",
        "Grounded explainability answer generated.",
        {"question": payload.question, **answer},
    )
    return answer


def _load_demand_or_404(demand_id: int) -> dict[str, Any]:
    demand = db.get_demand(demand_id)
    if demand is None:
        raise HTTPException(status_code=404, detail="Demand not found.")
    return demand


def _load_payload_or_404(table: str, demand_id: int, detail: str) -> dict[str, Any]:
    payload = db.get_payload(table, demand_id)
    if payload is None:
        raise HTTPException(status_code=409, detail=detail)
    return payload


def _collect_pipeline_state(demand: dict[str, Any]) -> dict[str, Any]:
    demand_id = demand["id"]
    return {
        "demand": demand,
        "analysis": db.get_payload("analyses", demand_id),
        "decision": db.get_payload("decisions", demand_id),
        "manager_assignment": db.get_payload("manager_assignments", demand_id),
        "team_plan": db.get_payload("team_plans", demand_id),
        "tracking_plan": db.get_payload("tracking_plans", demand_id),
        "notifications": db.get_payload("notifications", demand_id),
        "audit": db.list_audit_events(demand_id),
    }
