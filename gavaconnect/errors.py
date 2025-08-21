"""Error classes for the GavaConnect SDK."""

from __future__ import annotations


class SDKError(Exception):
    """Base exception for all SDK errors."""


class TransportError(SDKError):
    """Exception raised for network/transport related errors."""


class SerializationError(SDKError):
    """Exception raised for data serialization/deserialization errors."""


class APIError(SDKError):
    """Exception raised for API-related errors."""

    def __init__(
        self,
        status: int,
        type_: str,
        message: str,
        code: str | None,
        request_id: str | None,
        retry_after_s: float | None,
        body: bytes | None,
    ) -> None:
        """Initialize APIError with response details."""
        super().__init__(message)
        self.status = status
        self.type = type_
        self.code = code
        self.request_id = request_id
        self.retry_after_s = retry_after_s
        self.body = body


class RateLimitError(APIError):
    """Exception raised when API rate limits are exceeded."""
