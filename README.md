# OrchestrateAI - AI Demand Pipeline

OrchestrateAI is a FastAPI + SQLite web demo for the AI Club Demand Pipeline
Hackathon. It turns one messy AI demand into a complete, explainable pipeline:
intake, triage, routing, manager assignment, resource planning, rebalancing,
tracking, communications, and automation evidence.

## What We Built

- A polished single-page dashboard served by the same FastAPI app.
- A single-entry demand intake form with sample demands for quick demos.
- Gemini-powered demand analysis with a deterministic fallback if AI access is unavailable.
- Explainable routing to `Project`, `POC`, `Hackathon`, or `Partner`.
- Manager recommendation using expertise, capacity, and demand fit.
- Resource matching, team composition, reusable asset suggestions, and rebalance simulation.
- Stage tracking, SLA/risk visibility, notification drafts, audit trail, and `Ask why` explainability.

## How It Solves the Problem Statement

The problem statement asks for an end-to-end AI solution that reduces manual
effort across demand capture, triage, assignment, fulfilment, tracking, and reuse.
This app solves that by replacing scattered manual decisions with one automated
pipeline: a demand is captured once, classified, routed, assigned, staffed,
tracked, explained, and prepared for communication from the dashboard.

It also shows the required evidence: why each decision was made, which reusable
assets can speed delivery, what happens when a resource becomes unavailable, and
which manual steps were removed.

## Run Locally

```powershell
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open `http://127.0.0.1:8000`.

## How To Test

1. Load a sample demand.
2. Click `Create Demand`.
3. Click `Run AI Pipeline`.
4. Verify triage, route, manager, team, assets, timeline, comms drafts, evidence, and audit trail.
5. Click `Mark unavailable` on a team member to test automatic rebalancing.
6. Use `Ask why` to verify explainability.

Optional API checks:

```powershell
curl http://127.0.0.1:8000/api/health
curl http://127.0.0.1:8000/api/samples
```

## Notes

- Uses dummy data only.
- Gemini is used when configured; fallback logic keeps the demo usable without it.
- Notification drafts are generated for review only and are not sent.

