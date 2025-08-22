"""OpenTelemetry tracing utilities for HTTP requests."""

from typing import Any

import httpx

try:
    from opentelemetry import trace
    tracer = trace.get_tracer("gavaconnect")
    OTEL_AVAILABLE = True
except ImportError:
    # OpenTelemetry is optional - graceful degradation
    tracer: Any = None
    OTEL_AVAILABLE = False


async def otel_request_span(req: httpx.Request) -> None:
    """Start an OpenTelemetry span for an HTTP request.

    Args:
        req: The HTTP request to trace.

    """
    if not OTEL_AVAILABLE or tracer is None:
        return
    
    span = tracer.start_span(
        "http.client", attributes={"http.method": req.method, "http.url": str(req.url)}
    )
    req.extensions["otel_span"] = span


async def otel_response_span(req: httpx.Request, resp: httpx.Response) -> None:
    """Complete an OpenTelemetry span for an HTTP response.

    Args:
        req: The HTTP request.
        resp: The HTTP response.

    """
    if not OTEL_AVAILABLE:
        return
        
    span = req.extensions.pop("otel_span", None)
    if span:
        span.set_attribute("http.status_code", resp.status_code)
        rid = resp.headers.get("x-request-id")
        if rid:
            span.set_attribute("http.response.request_id", rid)
        span.end()
