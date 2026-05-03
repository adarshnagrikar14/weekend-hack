from __future__ import annotations

import json
import re
from typing import Any

from app.config import settings


ANALYSIS_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "domain": {"type": "string"},
        "priority": {"type": "string", "enum": ["Low", "Medium", "High", "Critical"]},
        "complexity": {"type": "string", "enum": ["Low", "Medium", "High"]},
        "required_skills": {"type": "array", "items": {"type": "string"}},
        "dependencies": {"type": "array", "items": {"type": "string"}},
        "sensitivity_flag": {"type": "string"},
        "quick_win": {"type": "boolean"},
        "net_new_innovation": {"type": "boolean"},
        "confidence": {"type": "number"},
        "clarifying_questions": {"type": "array", "items": {"type": "string"}},
        "summary": {"type": "string"},
    },
    "required": [
        "domain",
        "priority",
        "complexity",
        "required_skills",
        "dependencies",
        "sensitivity_flag",
        "quick_win",
        "net_new_innovation",
        "confidence",
        "clarifying_questions",
        "summary",
    ],
}


SKILL_KEYWORDS = {
    "Document AI": ["invoice", "document", "pdf", "form", "ocr", "contract"],
    "RAG": ["manual", "knowledge", "policy", "search", "answer", "assistant"],
    "GenAI": ["genai", "llm", "ai assistant", "prompt", "gemini", "copilot"],
    "Workflow Automation": ["route", "approval", "workflow", "triage", "manual"],
    "MLOps": ["monitor", "model", "production", "drift", "pipeline"],
    "Data Pipelines": ["forecast", "history", "sales", "data", "signals"],
    "Responsible AI": ["audit", "compliance", "risk", "governance", "sensitive"],
    "Live API": ["voice", "transcript", "call", "speak", "audio"],
    "FastAPI": ["api", "integration", "service", "backend"],
    "UX Engineering": ["dashboard", "portal", "interface", "user"],
}


DOMAIN_KEYWORDS = {
    "Document AI": ["invoice", "contract", "document", "pdf", "ocr"],
    "Demand Forecasting": ["forecast", "stockout", "sales", "sku", "planner"],
    "Knowledge Assistants": ["manual", "knowledge", "assistant", "field engineer"],
    "Workflow Automation": ["workflow", "approval", "triage", "route"],
    "Customer Service": ["call", "support", "customer", "ticket"],
    "Risk Analytics": ["risk", "fraud", "exception", "compliance"],
}


def analyze_demand(demand: dict[str, Any]) -> dict[str, Any]:
    fallback = heuristic_analysis(demand)
    if not settings.gemini_enabled:
        return fallback | {"engine": "heuristic-fallback", "model": None}

    try:
        from google import genai

        client = genai.Client(api_key=settings.gemini_api_key)
        prompt = _analysis_prompt(demand)
        response = client.models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_json_schema": ANALYSIS_SCHEMA,
            },
        )
        parsed = _parse_json(response.text)
        if not isinstance(parsed, dict):
            raise ValueError("Gemini returned a non-object response.")
        return _normalize_analysis(parsed) | {
            "engine": "gemini-structured-output",
            "model": settings.gemini_model,
        }
    except Exception as exc:  # Keep the hackathon demo reliable.
        return fallback | {
            "engine": "heuristic-fallback",
            "model": settings.gemini_model,
            "fallback_reason": str(exc)[:240],
        }


def _analysis_prompt(demand: dict[str, Any]) -> str:
    return f"""
You are an enterprise AI demand triage agent. Convert the demand into strict JSON.
Classify domain, priority, complexity, skills, dependencies, sensitivity, quick-win
fit, net-new innovation, confidence, and clarifying questions.

Demand:
Title: {demand.get("title")}
Requester: {demand.get("requester")}
Business unit: {demand.get("business_unit")}
Problem statement: {demand.get("problem_statement")}
Expected impact: {demand.get("expected_impact")}
Target date: {demand.get("target_date")}
Constraints: {demand.get("constraints")}
Optional skills: {demand.get("optional_skills")}
"""


def heuristic_analysis(demand: dict[str, Any]) -> dict[str, Any]:
    text = _joined_text(demand)
    skills = _match_keywords(text, SKILL_KEYWORDS)
    if not skills:
        skills = ["GenAI", "Workflow Automation", "UX Engineering"]

    domain_matches = _match_keywords(text, DOMAIN_KEYWORDS)
    domain = domain_matches[0] if domain_matches else "Workflow Automation"

    urgency = _extract_urgency_weeks(text)
    priority = "High" if urgency <= 4 else "Medium"
    if any(term in text for term in ["critical", "month-end", "regulatory", "risk"]):
        priority = "Critical"

    high_complexity_terms = ["production", "integration", "voice", "realtime", "sensitive"]
    complexity = "High" if any(term in text for term in high_complexity_terms) else "Medium"
    if urgency <= 3 and "prototype" in text:
        complexity = "Low"

    quick_win = urgency <= 4 or "prototype" in text or "quick" in text
    net_new = "new" in text or "voice" in text or "field" in text
    dependencies = _dependencies(text)

    confidence = 0.78
    if domain_matches:
        confidence += 0.08
    if len(skills) >= 3:
        confidence += 0.05

    return {
        "domain": domain,
        "priority": priority,
        "complexity": complexity,
        "required_skills": skills[:6],
        "dependencies": dependencies,
        "sensitivity_flag": "Dummy data only; human approval required for sensitive records."
        if any(term in text for term in ["compliance", "audit", "risk", "customer"])
        else "No sensitive data required for demo; confirm before production.",
        "quick_win": quick_win,
        "net_new_innovation": net_new and not quick_win,
        "confidence": min(round(confidence, 2), 0.94),
        "clarifying_questions": [
            "Which source systems will provide demand and workload data?",
            "Who approves the recommended fulfilment path before kickoff?",
        ],
        "summary": _summary(demand),
    }


def concise_explanation(question: str, context: dict[str, Any]) -> dict[str, str]:
    decision = context.get("decision") or {}
    manager = (context.get("manager_assignment") or {}).get("recommended_manager") or {}
    team = context.get("team_plan") or {}
    answer = (
        f"The pipeline chose {decision.get('route', 'the recommended route')} because "
        f"{', '.join(decision.get('reason_chips', [])[:3])}. "
        f"{manager.get('name', 'The selected manager')} leads due to workload and domain fit. "
        f"The team plan covers {len(team.get('team', []))} roles and keeps reusable assets first."
    )
    if "rebalance" in question.lower():
        answer = (
            "Rebalance removes the unavailable person, reruns hard constraints, then picks the "
            "next best fit while updating risk and timeline."
        )
    return {
        "mode": "text-grounded-explainability",
        "answer": answer,
        "voice_ready": "The same endpoint can be used behind a Gemini Live voice surface.",
    }


def _normalize_analysis(payload: dict[str, Any]) -> dict[str, Any]:
    fallback = heuristic_analysis(payload)
    normalized = fallback | payload
    normalized["required_skills"] = [
        str(skill).strip() for skill in normalized.get("required_skills", []) if str(skill).strip()
    ][:8]
    normalized["dependencies"] = [
        str(dep).strip() for dep in normalized.get("dependencies", []) if str(dep).strip()
    ][:8]
    normalized["confidence"] = max(0.0, min(float(normalized.get("confidence", 0.75)), 1.0))
    normalized["quick_win"] = bool(normalized.get("quick_win"))
    normalized["net_new_innovation"] = bool(normalized.get("net_new_innovation"))
    return normalized


def _parse_json(text: str | None) -> Any:
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        return json.loads(match.group(0)) if match else None


def _joined_text(demand: dict[str, Any]) -> str:
    return " ".join(str(value) for value in demand.values()).lower()


def _match_keywords(text: str, mapping: dict[str, list[str]]) -> list[str]:
    return [label for label, terms in mapping.items() if any(term in text for term in terms)]


def _extract_urgency_weeks(text: str) -> int:
    match = re.search(r"(\d+)\s*(week|weeks|wk|wks)", text)
    if match:
        return int(match.group(1))
    match = re.search(r"(\d+)\s*(day|days)", text)
    if match:
        return max(1, round(int(match.group(1)) / 7))
    return 6


def _dependencies(text: str) -> list[str]:
    deps = []
    if any(term in text for term in ["email", "invoice", "document", "manual"]):
        deps.append("Sample documents or knowledge source")
    if any(term in text for term in ["sales", "forecast", "data", "history"]):
        deps.append("Synthetic historical dataset")
    if any(term in text for term in ["approval", "route", "workflow"]):
        deps.append("Approval and routing policy")
    if any(term in text for term in ["voice", "call", "audio"]):
        deps.append("Voice transcript or Live API setup")
    return deps or ["Demand owner validation"]


def _summary(demand: dict[str, Any]) -> str:
    title = demand.get("title", "AI demand")
    impact = demand.get("expected_impact", "improve delivery outcomes")
    return f"{title}: {impact}"
