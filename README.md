# OrchestrateAI - AI Demand Pipeline

Polished FastAPI demo for the AI Club Demand Pipeline Hackathon. It converts a
single messy demand into AI triage, explainable routing, manager assignment,
resource fulfilment, rebalance, tracking, draft comms, and automation evidence.

## Run locally

```powershell
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open `http://127.0.0.1:8000`.

## Demo script

1. Load a sample demand.
2. Create the demand record.
3. Click `Run AI Pipeline`.
4. Review AI triage, route decision, manager recommendation, team plan, assets,
   timeline, notification drafts, and audit trail.
5. Click `Mark unavailable` on one resource to show automatic rebalancing.
6. Open the evidence panel to show manual steps removed and estimated effort
   saved.
7. Use `Ask why` to generate a grounded explanation of the decision.

## Notes

- Uses dummy data only.
- Gemini is used when `GEMINI_API_KEY` is available; deterministic fallback keeps
  the demo working without network access.
- Notification drafts are generated for evidence but are not sent.
