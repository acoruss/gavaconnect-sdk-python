"""
Error classes for the GavaConnect SDK.
"""

from __future__ import annotations


class SDKError(Exception): ...


class TransportError(SDKError): ...


class SerializationError(SDKError): ...


class APIError(SDKError):
    def __init__(
        self,
        status: int,
        type_: str,
        message: str,
        code: str | None,
        request_id: str | None,
        retry_after_s: float | None,
        body: bytes | None,
    ):
        super().__init__(message)
        self.status = status
        self.type = type_
        self.code = code
        self.request_id = request_id
        self.retry_after_s = retry_after_s
        self.body = body


class RateLimitError(APIError): ...
