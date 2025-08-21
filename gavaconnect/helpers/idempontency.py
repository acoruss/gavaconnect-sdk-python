"""Idempotency utilities for ensuring request uniqueness."""

import uuid


def idempotency_headers(key: str | None = None) -> dict[str, str]:
    """Generate idempotency headers for HTTP requests.

    Args:
        key: Optional idempotency key. If None, a UUID4 will be generated.

    Returns:
        A dictionary containing the idempotency-key header.

    """
    return {"idempotency-key": key or str(uuid.uuid4())}
