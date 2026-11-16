import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.telemetry import (
    AUTH_FAILURES_TOTAL,
    LINKS_CREATED_TOTAL,
    EXTRACTION_FAILURES_TOTAL,
    HTTP_REQUESTS_TOTAL,
)

client = TestClient(app)

def test_metrics_endpoint_available():
    """Verify Prometheus metrics endpoint is exposed and responds with 200."""
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]
    text = response.text
    assert "linksaver_http_requests_total" in text
    assert "linksaver_links_created_total" in text

def test_request_metrics_recorded():
    """Verify HTTP requests increment request counter and record status code."""
    # Hit health endpoint
    resp = client.get("/health")
    assert resp.status_code == 200

    # Read metrics
    metrics_resp = client.get("/metrics")
    assert 'endpoint="/health"' in metrics_resp.text
    assert 'status="200"' in metrics_resp.text

def test_auth_failure_metric_recorded():
    """Verify 401 Unauthorized triggers auth failure metric increment."""
    initial_val = AUTH_FAILURES_TOTAL._value.get()

    # Attempt to access protected endpoint without credentials
    resp = client.get("/api/v1/links")
    assert resp.status_code == 401

    updated_val = AUTH_FAILURES_TOTAL._value.get()
    assert updated_val > initial_val

def test_custom_metrics_structure():
    """Verify presence and valid label sets for application metrics."""
    # Test link created counter
    LINKS_CREATED_TOTAL.labels(site_type="youtube", domain="youtube.com").inc()
    metrics_resp = client.get("/metrics")
    assert 'linksaver_links_created_total{domain="youtube.com",site_type="youtube"}' in metrics_resp.text

    # Test extraction failure counter
    EXTRACTION_FAILURES_TOTAL.labels(extractor_type="ozon", error_type="TimeoutError").inc()
    metrics_resp2 = client.get("/metrics")
    assert 'linksaver_extraction_failures_total{error_type="TimeoutError",extractor_type="ozon"}' in metrics_resp2.text
