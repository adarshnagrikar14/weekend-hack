from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Callable

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app import db
from app.config import BASE_DIR, settings
from app.schemas import (
    DemandCreate,
    ExplainRequest,
    LoginRequest,
    RebalanceRequest,
    RegisterRequest,
)
from app.services import data_loader
from app.services.auth_service import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
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

bearer_scheme = HTTPBearer(auto_error=False)


def _safe_user(user: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": user["id"],
        "username": user["username"],
        "display_name": user["display_name"],
        "role": user["role"],
        "is_active": bool(user["is_active"]),
        "created_at": user["created_at"],
        "last_login_at": user.get("last_login_at"),
    }


def _current_user(credentials: HTTPAuthorizationCredentials | None) -> dict[str, Any]:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Authentication required.")
    try:
        payload = decode_access_token(credentials.credentials)
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=401, detail="Invalid or expired token.") from exc
    user_id = int(payload.get("sub", 0))
    user = db.get_user_by_id(user_id)
    if user is None or not user["is_active"]:
        raise HTTPException(status_code=401, detail="User not found or inactive.")
    return user


def _optional_current_user(request: Request) -> dict[str, Any] | None:
    auth = request.headers.get("authorization", "")
    if not auth.lower().startswith("bearer "):
        return None
    token = auth.split(" ", 1)[1]
    try:
        payload = decode_access_token(token)
    except Exception:
        return None
    user_id = int(payload.get("sub", 0))
    return db.get_user_by_id(user_id)


def _require_roles(*roles: str) -> Callable[[HTTPAuthorizationCredentials | None], dict[str, Any]]:
    role_set = set(roles)

    def dependency(
        credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    ) -> dict[str, Any]:
        user = _current_user(credentials)
        if user["role"] not in role_set:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{user['role']}' cannot access this endpoint.",
            )
        return user

    return dependency


def _ensure_default_admin() -> None:
    existing = db.get_user_by_username("admin")
    if existing:
        if not str(existing.get("password_hash", "")).startswith("pbkdf2_sha256$"):
            bootstrap_password = os.getenv("AUTH_BOOTSTRAP_PASSWORD", "admin123")
            db.update_user_password(existing["id"], hash_password(bootstrap_password))
        return
    bootstrap_password = os.getenv("AUTH_BOOTSTRAP_PASSWORD", "admin123")
    db.create_user(
        username="admin",
        display_name="Platform Admin",
        password_hash=hash_password(bootstrap_password),
        role="admin",
    )


@app.on_event("startup")
def startup() -> None:
    db.init_db()
    _ensure_default_admin()


@app.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "index.html",
        context={
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
def samples(user: dict[str, Any] = Depends(_require_roles("admin", "manager", "analyst", "viewer"))) -> list[dict[str, Any]]:
    db.add_user_activity(user["id"], "samples_viewed", "Sample demands viewed.")
    return data_loader.sample_demands()


@app.post("/api/demands")
def create_demand(
    payload: DemandCreate,
    user: dict[str, Any] = Depends(_require_roles("admin", "manager", "analyst")),
) -> dict[str, Any]:
    demand = db.insert_demand(payload.model_dump(), created_by=user["id"])
    db.add_user_activity(
        user["id"], "demand_created", f"Demand #{demand['id']} created.", {"demand_id": demand["id"]}
    )
    return {"demand": demand, "audit": db.list_audit_events(demand["id"])}


@app.get("/api/demands/{demand_id}")
def get_demand(
    demand_id: int,
    user: dict[str, Any] = Depends(_require_roles("admin", "manager", "analyst", "viewer")),
) -> dict[str, Any]:
    demand = _load_demand_or_404(demand_id)
    db.add_user_activity(user["id"], "demand_viewed", f"Demand #{demand_id} viewed.", {"demand_id": demand_id})
    return _collect_pipeline_state(demand)


@app.post("/api/demands/{demand_id}/run")
def run_pipeline(
    demand_id: int,
    user: dict[str, Any] = Depends(_require_roles("admin", "manager", "analyst")),
) -> dict[str, Any]:
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
    db.add_user_activity(
        user["id"],
        "pipeline_run",
        f"Pipeline run completed for demand #{demand_id}.",
        {"demand_id": demand_id, "route": decision["route"]},
    )
    return _collect_pipeline_state(_load_demand_or_404(demand_id))


@app.post("/api/demands/{demand_id}/rebalance")
def rebalance(
    demand_id: int,
    payload: RebalanceRequest,
    user: dict[str, Any] = Depends(_require_roles("admin", "manager", "analyst")),
) -> dict[str, Any]:
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
    db.add_user_activity(
        user["id"],
        "rebalance_run",
        f"Rebalance simulated for demand #{demand_id}.",
        {"demand_id": demand_id, "removed_resource_id": payload.removed_resource_id},
    )
    return _collect_pipeline_state(_load_demand_or_404(demand_id))


@app.post("/api/voice/explain")
def explain(
    payload: ExplainRequest,
    user: dict[str, Any] = Depends(_require_roles("admin", "manager", "analyst", "viewer")),
) -> dict[str, str]:
    demand = _load_demand_or_404(payload.demand_id)
    context = _collect_pipeline_state(demand)
    answer = concise_explanation(payload.question, context)
    db.add_audit_event(
        payload.demand_id,
        "voice_explainability",
        "Grounded explainability answer generated.",
        {"question": payload.question, **answer},
    )
    db.add_user_activity(
        user["id"],
        "decision_explained",
        f"Explainability answer generated for demand #{payload.demand_id}.",
        {"demand_id": payload.demand_id},
    )
    return answer


@app.post("/api/auth/register")
def register(payload: RegisterRequest, request: Request) -> dict[str, Any]:
    existing = db.get_user_by_username(payload.username)
    if existing:
        raise HTTPException(status_code=409, detail="Username already exists.")

    maybe_user = _optional_current_user(request)
    target_role = payload.role
    if not maybe_user or maybe_user["role"] != "admin":
        if payload.role in {"admin", "manager"}:
            raise HTTPException(status_code=403, detail="Only admins can create privileged roles.")
        target_role = "analyst"

    user = db.create_user(
        username=payload.username.strip(),
        display_name=payload.display_name.strip(),
        password_hash=hash_password(payload.password),
        role=target_role,
    )
    db.add_auth_event(
        username=user["username"],
        event_type="register",
        success=True,
        detail="Account created.",
        user_id=user["id"],
        ip_address=request.client.host if request.client else "",
        user_agent=request.headers.get("user-agent", ""),
    )
    return {"user": _safe_user(user)}


@app.post("/api/auth/login")
def login(payload: LoginRequest, request: Request) -> dict[str, Any]:
    user = db.get_user_by_username(payload.username)
    if user is None or not verify_password(payload.password, user["password_hash"]):
        db.add_auth_event(
            username=payload.username,
            event_type="login",
            success=False,
            detail="Invalid credentials.",
            ip_address=request.client.host if request.client else "",
            user_agent=request.headers.get("user-agent", ""),
        )
        raise HTTPException(status_code=401, detail="Invalid username or password.")

    if not user["is_active"]:
        raise HTTPException(status_code=403, detail="User account is inactive.")

    db.set_user_last_login(user["id"])
    token = create_access_token(user)
    db.add_auth_event(
        username=user["username"],
        event_type="login",
        success=True,
        detail="Login successful.",
        user_id=user["id"],
        ip_address=request.client.host if request.client else "",
        user_agent=request.headers.get("user-agent", ""),
    )
    db.add_user_activity(user["id"], "login", "User logged in.")
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in_minutes": settings.access_token_minutes,
        "user": _safe_user(user),
    }


@app.post("/api/auth/logout")
def logout(
    request: Request,
    user: dict[str, Any] = Depends(_require_roles("admin", "manager", "analyst", "viewer")),
) -> dict[str, str]:
    db.add_auth_event(
        username=user["username"],
        event_type="logout",
        success=True,
        detail="Logout requested.",
        user_id=user["id"],
        ip_address=request.client.host if request.client else "",
        user_agent=request.headers.get("user-agent", ""),
    )
    db.add_user_activity(user["id"], "logout", "User logged out.")
    return {"status": "ok"}


@app.get("/api/auth/me")
def me(user: dict[str, Any] = Depends(_require_roles("admin", "manager", "analyst", "viewer"))) -> dict[str, Any]:
    return {"user": _safe_user(user)}


@app.get("/api/auth/history")
def history(
    user: dict[str, Any] = Depends(_require_roles("admin", "manager", "analyst", "viewer")),
) -> dict[str, Any]:
    return {"events": db.list_user_activity(user["id"], limit=80)}


@app.get("/api/auth/stats")
def auth_stats(
    user: dict[str, Any] = Depends(_require_roles("admin", "manager")),
) -> dict[str, Any]:
    db.add_user_activity(user["id"], "stats_viewed", "Auth and usage stats viewed.")
    return db.auth_stats()


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
