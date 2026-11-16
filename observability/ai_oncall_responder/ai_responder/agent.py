import datetime
import json
import logging
import uuid
from typing import List, Dict, Any

from ai_responder.config import settings
from ai_responder.schemas import AlertmanagerWebhook, IncidentReport

logger = logging.getLogger("ai_oncall_agent")

SYSTEM_INSTRUCTION = """
You are an expert Principal Site Reliability Engineer (SRE) and autonomous AI On-Call Incident Responder for the Link Saver web application.
The application stack is:
- Frontend: React SPA (Vite + Tailwind CSS)
- Backend: FastAPI (Python 3.11+, SQLAlchemy relational model)
- Database: PostgreSQL 16 (dockerized)
- Video Streaming: yt-dlp on-demand 720p streaming pipeline
- Scrapers: E-commerce extraction for Ozon, Wildberries, AliExpress via BHAPI + OpenGraph fallback
- Telemetry: OpenTelemetry SDK + Collector, Prometheus, Grafana, Alertmanager

Your objective:
1. Classify incident severity: 'P1_CRITICAL', 'P2_HIGH', 'P3_MEDIUM', or 'P4_LOW'.
2. Provide a concise 1-sentence summary of the incident.
3. List all affected components.
4. Diagnose the most probable root cause based on alert annotations, metrics, and labels.
5. Assess user and business impact.
6. Provide concrete, step-by-step remediation commands and runbook actions.
7. Provide long-term architectural or operational prevention recommendations.

Respond ONLY with a valid JSON object matching this structure:
{
  "severity": "P1_CRITICAL | P2_HIGH | P3_MEDIUM | P4_LOW",
  "summary": "One sentence summary",
  "affected_components": ["component1", "component2"],
  "probable_root_cause": "Detailed technical root cause explanation",
  "impact_assessment": "How users and services are impacted",
  "remediation_steps": ["step 1", "step 2", "step 3"],
  "prevention_recommendations": ["prevention 1", "prevention 2"]
}
"""


class AIIncidentAgent:
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.model_name = settings.GEMINI_MODEL
        self._genai_client = None

        if self.api_key:
            try:
                from google import genai
                self._genai_client = genai.Client(api_key=self.api_key)
                logger.info("Google GenAI client initialized for AI On-Call Responder")
            except Exception as e:
                logger.warning(f"Could not initialize GenAI client: {e}")

    async def triage_alert(self, payload: AlertmanagerWebhook) -> IncidentReport:
        incident_id = f"inc-{uuid.uuid4().hex[:8]}"
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        is_resolved = payload.status == "resolved"

        # Check if all alerts are resolved
        if is_resolved:
            return IncidentReport(
                incident_id=incident_id,
                created_at=now,
                status="resolved",
                severity="P4_LOW",
                summary="Alert condition resolved. All system metrics have returned to nominal baseline.",
                affected_components=list(set([a.labels.get("component", "system") for a in payload.alerts])),
                probable_root_cause="Transient spike or automated self-healing returned metric within thresholds.",
                impact_assessment="No lingering user impact detected.",
                remediation_steps=["Verify Prometheus graph baseline", "Close incident ticket"],
                prevention_recommendations=["Review threshold window if flap occurs repeatedly"],
                raw_alert_count=len(payload.alerts),
            )

        # Attempt Gemini analysis if API key is provided
        if self._genai_client:
            try:
                report = await self._query_gemini(payload, incident_id, now)
                if report:
                    return report
            except Exception as e:
                logger.error(f"Gemini triage failed, falling back to heuristic engine: {e}")

        # Intelligent Heuristic Fallback Engine
        return self._heuristic_triage(payload, incident_id, now)

    async def _query_gemini(self, payload: AlertmanagerWebhook, incident_id: str, timestamp: str) -> IncidentReport:
        prompt = f"""
Incoming Alertmanager Alert:
Status: {payload.status}
Common Labels: {json.dumps(payload.commonLabels)}
Common Annotations: {json.dumps(payload.commonAnnotations)}
Alert Details:
{json.dumps([a.model_dump() for a in payload.alerts], indent=2)}

Please analyze this incident and return the structured JSON triage report.
"""
        response = self._genai_client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config={
                "system_instruction": SYSTEM_INSTRUCTION,
                "response_mime_type": "application/json",
            }
        )

        data = json.loads(response.text)
        return IncidentReport(
            incident_id=incident_id,
            created_at=timestamp,
            status="investigating",
            severity=data.get("severity", "P2_HIGH"),
            summary=data.get("summary", "Automated incident detected by alert rule."),
            affected_components=data.get("affected_components", ["backend"]),
            probable_root_cause=data.get("probable_root_cause", "Anomaly in telemetry metrics."),
            impact_assessment=data.get("impact_assessment", "Potential degradation of service."),
            remediation_steps=data.get("remediation_steps", ["Check container logs", "Inspect metrics dashboard"]),
            prevention_recommendations=data.get("prevention_recommendations", ["Add automated regression tests"]),
            raw_alert_count=len(payload.alerts),
        )

    def _heuristic_triage(self, payload: AlertmanagerWebhook, incident_id: str, timestamp: str) -> IncidentReport:
        alert_names = [a.labels.get("alertname", "") for a in payload.alerts]
        components = list(set([a.labels.get("component", "backend") for a in payload.alerts]))

        if any("High5xxErrorRate" in name for name in alert_names):
            return IncidentReport(
                incident_id=incident_id,
                created_at=timestamp,
                status="action_required",
                severity="P1_CRITICAL",
                summary="Critical server error spike: API returning elevated 5xx responses.",
                affected_components=["backend-api", "database"],
                probable_root_cause="Unhandled exception in FastAPI request handlers, PostgreSQL connection exhaustion, or missing environment secrets.",
                impact_assessment="Users may experience failed link saves, login rejections, and broken dashboard interactions.",
                remediation_steps=[
                    "Inspect backend container logs: `docker compose -f docker-compose.prod.yml logs --tail=100 app`",
                    "Verify PostgreSQL health: `docker exec linksaver-db-prod pg_isready`",
                    "Restart backend container if stuck: `docker compose -f docker-compose.prod.yml restart app`",
                    "Check database connection pool limits in `backend/app/db/session.py`"
                ],
                prevention_recommendations=[
                    "Implement circuit breaker and connection pooling retries",
                    "Add automated synthetic canary monitoring on `/health` and `/api/v1/auth/me`"
                ],
                raw_alert_count=len(payload.alerts),
            )

        if any("MarketplaceExtractorFailure" in name for name in alert_names):
            return IncidentReport(
                incident_id=incident_id,
                created_at=timestamp,
                status="action_required",
                severity="P2_HIGH",
                summary="Marketplace e-commerce metadata extraction failure spike (Ozon/Wildberries/AliExpress).",
                affected_components=["marketplace-scrapers", "bhapi-client"],
                probable_root_cause="BHAPI token quota exhausted, invalid upstream credentials, or marketplace anti-bot layout changes.",
                impact_assessment="Saving Ozon or Wildberries URLs falls back to generic OpenGraph scraper, resulting in missing item prices or specifications.",
                remediation_steps=[
                    "Check BHAPI token validity: `curl -H 'Authorization: Bearer $BHAPI_TOKEN' https://bhapi.ru/api/balance`",
                    "Verify extractor fallback responses in backend logs",
                    "Renew or top up BHAPI account balance if quota exceeded",
                    "Verify OpenGraph fallback parser is active"
                ],
                prevention_recommendations=[
                    "Implement balance threshold alerts on BHAPI account",
                    "Cache product metadata in Redis / PostgreSQL to minimize redundant upstream requests"
                ],
                raw_alert_count=len(payload.alerts),
            )

        if any("YouTubeDownloadFailure" in name for name in alert_names):
            return IncidentReport(
                incident_id=incident_id,
                created_at=timestamp,
                status="action_required",
                severity="P2_HIGH",
                summary="YouTube 720p video streaming pipeline failures detected.",
                affected_components=["youtube-streaming", "yt-dlp", "ffmpeg"],
                probable_root_cause="YouTube cipher signature rotation, outdated yt-dlp binary, or missing ffmpeg muxing binaries on host.",
                impact_assessment="Users are unable to download 720p YouTube MP4 videos from their saved link cards.",
                remediation_steps=[
                    "Update yt-dlp to latest version: `pip install --upgrade yt-dlp`",
                    "Verify ffmpeg binary location and Node.js runtime availability",
                    "Check backend disk space for temp directory: `df -h /tmp`",
                    "Test manual stream generation using test video URL"
                ],
                prevention_recommendations=[
                    "Schedule weekly automated yt-dlp dependency update in CI/CD",
                    "Implement secondary streaming fallback or format downgrades (e.g. 480p)"
                ],
                raw_alert_count=len(payload.alerts),
            )

        if any("HighAuthFailureRate" in name for name in alert_names):
            return IncidentReport(
                incident_id=incident_id,
                created_at=timestamp,
                status="investigating",
                severity="P2_HIGH",
                summary="Elevated rate of authentication failures (401) detected.",
                affected_components=["auth-service", "security"],
                probable_root_cause="Potential credential stuffing attack, brute force attempts, or expired client tokens.",
                impact_assessment="Risk of account takeover if brute force succeeds; potential load spike on password hashing functions.",
                remediation_steps=[
                    "Inspect remote client IPs from access logs to identify attack origins",
                    "Consider temporary IP rate limiting or Cloudflare WAF block",
                    "Verify bcrypt hashing work factor isn't exhausting backend CPU"
                ],
                prevention_recommendations=[
                    "Introduce Redis-backed rate limiting per IP / account",
                    "Implement account lockout after 5 consecutive failed attempts"
                ],
                raw_alert_count=len(payload.alerts),
            )

        # Default fallback
        return IncidentReport(
            incident_id=incident_id,
            created_at=timestamp,
            status="investigating",
            severity="P3_MEDIUM",
            summary=f"Alert triggered: {', '.join(alert_names) or 'System Metric Alert'}",
            affected_components=components,
            probable_root_cause="Metric threshold exceeded configured boundary.",
            impact_assessment="Non-critical component degradation.",
            remediation_steps=[
                "Review Grafana APM dashboard at http://localhost:3000",
                "Check recent system deployments and commit logs"
            ],
            prevention_recommendations=["Tune alert threshold duration to prevent false positives"],
            raw_alert_count=len(payload.alerts),
        )
