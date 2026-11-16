import logging
from typing import List
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from ai_responder.config import settings
from ai_responder.schemas import AlertmanagerWebhook, IncidentReport
from ai_responder.agent import AIIncidentAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ai_oncall_responder")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="Autonomous AI Agent On-Call Responder for Link Saver Incidents and Telemetry Alerts",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

agent = AIIncidentAgent()
incidents_history: List[IncidentReport] = []


@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "ok",
        "service": settings.PROJECT_NAME,
        "gemini_enabled": bool(settings.GEMINI_API_KEY),
        "total_triaged_incidents": len(incidents_history),
    }


@app.post("/webhook/alert", response_model=IncidentReport, status_code=status.HTTP_200_OK, tags=["Alerts"])
async def receive_alert_webhook(payload: AlertmanagerWebhook):
    """
    Receives alert webhook from Prometheus Alertmanager or Grafana Alerting.
    Triggers the AI Incident Agent to classify, diagnose root cause, and provide remediation.
    """
    logger.info(f"Received alert webhook: status={payload.status}, alerts={len(payload.alerts)}")
    report = await agent.triage_alert(payload)

    # Prepend to incident history
    incidents_history.insert(0, report)

    logger.info(f"Generated incident triage {report.incident_id} (Severity: {report.severity})")
    return report


@app.get("/incidents", response_model=List[IncidentReport], tags=["Incidents"])
async def list_incidents():
    """Returns past and active triaged incident reports."""
    return incidents_history


@app.get("/incidents/{incident_id}", response_model=IncidentReport, tags=["Incidents"])
async def get_incident(incident_id: str):
    """Returns details for a specific incident report."""
    for inc in incidents_history:
        if inc.incident_id == incident_id:
            return inc
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=True)
