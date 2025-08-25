"""OpenTelemetry tracing utilities for HTTP requests."""

import httpx

try:
    from opentelemetry import trace  # pragma: no cover

    tracer: trace.Tracer | None = trace.get_tracer("gavaconnect")  # pragma: no cover
    OTEL_AVAILABLE = True  # pragma: no cover
except ImportError:  # pragma: no cover
    # OpenTelemetry is optional - graceful degradation
    tracer = None
    OTEL_AVAILABLE = False


async def otel_request_span(req: httpx.Request) -> None:
    """Start an OpenTelemetry span for an HTTP request.

    Args:
        req: The HTTP request to trace.

    """
    if not OTEL_AVAILABLE or tracer is None:
        return

    span = tracer.start_span(  # pragma: no cover
        "http.client",
        attributes={
            "http.method": req.method,
            "http.url": str(req.url),
        },  # pragma: no cover
    )  # pragma: no cover
    req.extensions["otel_span"] = span  # pragma: no cover


async def otel_response_span(req: httpx.Request, resp: httpx.Response) -> None:
    """Complete an OpenTelemetry span for an HTTP response.

    Args:
        req: The HTTP request.
        resp: The HTTP response.

    """
    if not OTEL_AVAILABLE:
        return

    span = req.extensions.pop("otel_span", None)  # pragma: no cover
    if span:  # pragma: no cover
        span.set_attribute("http.status_code", resp.status_code)  # pragma: no cover
        rid = resp.headers.get("x-request-id")  # pragma: no cover
        if rid:  # pragma: no cover
            span.set_attribute("http.response.request_id", rid)  # pragma: no cover
        span.end()  # pragma: no cover
