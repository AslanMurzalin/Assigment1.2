import logging
import time
from typing import Callable
from fastapi import FastAPI, Request, Response
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

from app.core.config import settings

logger = logging.getLogger("telemetry")

# Prometheus custom metrics
HTTP_REQUESTS_TOTAL = Counter(
    "linksaver_http_requests_total",
    "Total HTTP requests received",
    ["method", "endpoint", "status"],
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "linksaver_http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
)

LINKS_CREATED_TOTAL = Counter(
    "linksaver_links_created_total",
    "Total links saved in Link Saver",
    ["site_type", "domain"],
)

EXTRACTION_DURATION_SECONDS = Histogram(
    "linksaver_extraction_duration_seconds",
    "Duration of metadata extraction in seconds",
    ["extractor_type"],
)

EXTRACTION_FAILURES_TOTAL = Counter(
    "linksaver_extraction_failures_total",
    "Total failed metadata extractions",
    ["extractor_type", "error_type"],
)

YOUTUBE_DOWNLOADS_TOTAL = Counter(
    "linksaver_youtube_downloads_total",
    "Total YouTube video download attempts",
    ["status"],
)

YOUTUBE_DOWNLOAD_DURATION_SECONDS = Histogram(
    "linksaver_youtube_download_duration_seconds",
    "Duration of YouTube downloads in seconds",
)

AUTH_FAILURES_TOTAL = Counter(
    "linksaver_auth_failures_total",
    "Total authentication failures (401)",
)


def setup_telemetry(app: FastAPI):
    """Initialize OpenTelemetry tracer and register Prometheus middleware & endpoint."""
    import os
    import sys

    is_test = "pytest" in sys.modules or os.getenv("ENV") == "test" or os.getenv("PYTEST_CURRENT_TEST")

    if settings.OTEL_ENABLED and not is_test:
        try:
            from opentelemetry import trace
            from opentelemetry.sdk.trace import TracerProvider
            from opentelemetry.sdk.trace.export import BatchSpanProcessor
            from opentelemetry.sdk.resources import Resource
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
            from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

            resource = Resource.create({"service.name": settings.OTEL_SERVICE_NAME})
            provider = TracerProvider(resource=resource)

            # Only attach remote OTLP exporter if endpoint is configured and not in test
            if settings.OTEL_EXPORTER_OTLP_ENDPOINT:
                exporter = OTLPSpanExporter(
                    endpoint=settings.OTEL_EXPORTER_OTLP_ENDPOINT,
                    insecure=True,
                )
                provider.add_span_processor(BatchSpanProcessor(exporter))

            trace.set_tracer_provider(provider)
            FastAPIInstrumentor.instrument_app(app, tracer_provider=provider)
            logger.info(f"OpenTelemetry initialized for service: {settings.OTEL_SERVICE_NAME}")
        except Exception as e:
            logger.warning(f"OpenTelemetry initialization skipped/failed: {e}")

    # Register metrics scraping endpoint
    @app.get("/metrics", tags=["Observability"], include_in_schema=False)
    async def metrics():
        return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

    # Middleware for Prometheus HTTP request tracking
    @app.middleware("http")
    async def prometheus_metrics_middleware(request: Request, call_next: Callable):
        start_time = time.time()
        # Clean path for metric label (skip query string and group specific IDs)
        endpoint = request.url.path
        if endpoint == "/metrics":
            return await call_next(request)

        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception:
            status_code = 500
            raise
        finally:
            duration = time.time() - start_time
            HTTP_REQUESTS_TOTAL.labels(
                method=request.method,
                endpoint=endpoint,
                status=str(status_code),
            ).inc()
            HTTP_REQUEST_DURATION_SECONDS.labels(
                method=request.method,
                endpoint=endpoint,
            ).observe(duration)

            if status_code == 401:
                AUTH_FAILURES_TOTAL.inc()

        return response
