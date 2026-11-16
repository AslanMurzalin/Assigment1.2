import sys
import os
import pytest
from fastapi.testclient import TestClient

# Ensure ai_oncall_responder app is in python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from ai_responder.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "Link Saver" in data["service"]


def test_high_5xx_incident_triage():
    payload = {
        "version": "4",
        "status": "firing",
        "alerts": [
            {
                "status": "firing",
                "labels": {
                    "alertname": "High5xxErrorRate",
                    "severity": "critical",
                    "service": "linksaver-api",
                    "component": "backend"
                },
                "annotations": {
                    "summary": "High HTTP 5xx error rate detected on Link Saver API",
                    "description": "Link Saver backend is returning 5xx server errors at an elevated rate."
                }
            }
        ]
    }
    response = client.post("/webhook/alert", json=payload)
    assert response.status_code == 200
    incident = response.json()
    assert incident["severity"] == "P1_CRITICAL"
    assert "5xx" in incident["summary"]
    assert "backend-api" in incident["affected_components"]
    assert len(incident["remediation_steps"]) > 0


def test_marketplace_incident_triage():
    payload = {
        "version": "4",
        "status": "firing",
        "alerts": [
            {
                "status": "firing",
                "labels": {
                    "alertname": "MarketplaceExtractorFailure",
                    "severity": "warning",
                    "service": "linksaver-extractors",
                    "component": "marketplace-scrapers"
                },
                "annotations": {
                    "summary": "Marketplace product extraction failures detected",
                    "description": "E-commerce metadata extraction failed for Ozon."
                }
            }
        ]
    }
    response = client.post("/webhook/alert", json=payload)
    assert response.status_code == 200
    incident = response.json()
    assert incident["severity"] in ["P2_HIGH", "P3_MEDIUM"]
    assert "Marketplace" in incident["summary"] or "extraction" in incident["summary"].lower()
    assert any("BHAPI" in step or "curl" in step for step in incident["remediation_steps"])


def test_youtube_streaming_incident_triage():
    payload = {
        "version": "4",
        "status": "firing",
        "alerts": [
            {
                "status": "firing",
                "labels": {
                    "alertname": "YouTubeDownloadFailure",
                    "severity": "warning",
                    "service": "linksaver-streaming",
                    "component": "youtube-downloader"
                },
                "annotations": {
                    "summary": "YouTube video download stream failure",
                    "description": "Failures occurred while extracting or streaming YouTube 720p video."
                }
            }
        ]
    }
    response = client.post("/webhook/alert", json=payload)
    assert response.status_code == 200
    incident = response.json()
    assert incident["severity"] == "P2_HIGH"
    assert "YouTube" in incident["summary"]
    assert any("yt-dlp" in step for step in incident["remediation_steps"])


def test_resolved_alert_handling():
    payload = {
        "version": "4",
        "status": "resolved",
        "alerts": [
            {
                "status": "resolved",
                "labels": {
                    "alertname": "High5xxErrorRate",
                    "severity": "critical",
                    "component": "backend"
                },
                "annotations": {
                    "summary": "High HTTP 5xx error rate resolved."
                }
            }
        ]
    }
    response = client.post("/webhook/alert", json=payload)
    assert response.status_code == 200
    incident = response.json()
    assert incident["status"] == "resolved"
    assert incident["severity"] == "P4_LOW"


def test_list_and_get_incidents():
    list_resp = client.get("/incidents")
    assert list_resp.status_code == 200
    incidents = list_resp.json()
    assert len(incidents) > 0

    target_id = incidents[0]["incident_id"]
    get_resp = client.get(f"/incidents/{target_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["incident_id"] == target_id
