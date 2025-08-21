"""HTTP request and response logging utilities."""

import logging
import time

import httpx

logger = logging.getLogger("gavaconnect")


async def log_request(req: httpx.Request) -> None:
    """Log an HTTP request with sanitized headers.

    Args:
        req: The HTTP request to log.

    """
    req.extensions["start_time"] = time.perf_counter()
    hdrs = dict(req.headers)
    hdrs.pop("authorization", None)
    logger.debug(f"HTTP {req.method} {req.url} headers={hdrs}")


async def log_response(req: httpx.Request, resp: httpx.Response) -> None:
    """Log an HTTP response with timing information.

    Args:
        req: The HTTP request.
        resp: The HTTP response to log.

    """
    dur = time.perf_counter() - req.extensions.get("start_time", time.perf_counter())
    logger.info(
        f"HTTP {req.method} {req.url} -> {resp.status_code} in {dur:.3f}s request_id={resp.headers.get('x-request-id')}"
    )
