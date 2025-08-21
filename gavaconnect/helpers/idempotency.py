"""Idempotency utilities for ensuring request uniqueness."""

import datetime
import uuid
from email.utils import parsedate_to_datetime
from random import SystemRandom

import httpx

_rng = SystemRandom()  # cryptographically strong; avoids Bandit B311


def idempotency_headers(key: str | None = None) -> dict[str, str]:
    """Generate idempotency headers for HTTP requests.

    Args:
        key: Optional idempotency key. If None, a UUID4 will be generated.

    Returns:
        A dictionary containing the idempotency-key header.

    """
    return {"idempotency-key": key or str(uuid.uuid4())}


def _full_jitter(base: float, attempt: int, cap: float) -> float:
    """AWS-style full jitter: sleep ~ U(0, min(cap, base*2^attempt))."""
    max_sleep = min(cap, base * (2**attempt))
    return _rng.uniform(0.0, max_sleep)


def _parse_retry_after(value: str | None) -> float | None:
    """Return seconds to wait from Retry-After which may be seconds or HTTP-date."""
    if not value:
        return None
    # numeric seconds
    try:
        secs = float(value)
        if secs >= 0:
            return secs
    except ValueError:
        pass
    # HTTP-date
    try:
        dt = parsedate_to_datetime(value)
        if dt is not None:
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=datetime.UTC)
            delta = (dt - datetime.datetime.now(datetime.UTC)).total_seconds()
            return max(0.0, delta)
    except Exception:
        return None


def _is_idempotent(method: str) -> bool:
    return method.upper() in {"GET", "HEAD", "OPTIONS", "DELETE"}


def _can_retry(method: str, req: httpx.Request) -> bool:
    # Allow retries for idempotent methods, or if caller provides Idempotency-Key for writes.
    return _is_idempotent(method) or (
        "idempotency-key" in (k.lower() for k in req.headers.keys())
    )
