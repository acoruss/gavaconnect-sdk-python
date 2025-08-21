"""HTTP transport implementation with retry logic and error handling."""

from __future__ import annotations

import asyncio
import random
from typing import Any

import httpx

from gavaconnect.auth import AuthPolicy
from gavaconnect.config import SDKConfig
from gavaconnect.errors import APIError, RateLimitError, TransportError


def _jitter(base: float, attempt: int) -> float:
    return float(base * (2 ** (attempt - 1)) * (1 + random.random() * 0.2))


class AsyncTransport:
    """Async HTTP transport with retry logic and authentication support."""

    def __init__(self, cfg: SDKConfig) -> None:
        """Initialize the async transport.

        Args:
            cfg: SDK configuration containing timeout and retry settings.

        """
        self.cfg = cfg
        self.client = httpx.AsyncClient(
            base_url=cfg.base_url,
            http2=True,
            timeout=httpx.Timeout(
                cfg.total_timeout_s,
                read=cfg.read_timeout_s,
                connect=cfg.connect_timeout_s,
            ),
            headers={"user-agent": cfg.user_agent, "x-client-version": cfg.user_agent},
        )

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self.client.aclose()

    async def request(
        self, method: str, url: str, *, auth: AuthPolicy | None = None, **kw: Any
    ) -> httpx.Response:
        """Make an HTTP request with retry logic and authentication.

        Args:
            method: HTTP method (GET, POST, etc.).
            url: Request URL.
            auth: Optional authentication policy.
            **kw: Additional keyword arguments for the request.

        Returns:
            The HTTP response.

        Raises:
            TransportError: If the request fails after all retries.

        """
        req = self.client.build_request(method, url, **kw)
        if auth:
            await auth.authorize(req)
        attempt = 1
        while True:
            try:
                resp = await self.client.send(req, stream=False)
            except httpx.HTTPError as e:
                if attempt > self.cfg.retry.max_attempts:
                    raise TransportError(str(e)) from e
                await asyncio.sleep(_jitter(self.cfg.retry.base_backoff_s, attempt))
                attempt += 1
                continue
            if resp.status_code == 401 and auth and await auth.on_unauthorized():
                req = self.client.build_request(method, url, **kw)
                await auth.authorize(req)
                resp = await self.client.send(req, stream=False)
            if (
                resp.status_code in self.cfg.retry.retry_on_status
                and attempt <= self.cfg.retry.max_attempts
            if self._should_retry_on_status(resp, attempt):
                ra = resp.headers.get("retry-after")
                backoff = (
                    float(ra)
                    if ra and ra.isdigit()
                    else _jitter(self.cfg.retry.base_backoff_s, attempt)
                )
                await asyncio.sleep(backoff)
                attempt += 1
                continue
            return resp

    @staticmethod
    def raise_for_api_error(resp: httpx.Response) -> None:
        """Raise appropriate API error based on response status and content.

        Args:
            resp: HTTP response to check for errors.

        Raises:
            APIError: For general API errors.
            RateLimitError: For rate limit errors (status 429).

        """
        if resp.status_code < 400:
            return
        try:
            b = resp.json()
            err = b.get("error", {})
        except (json.JSONDecodeError, ValueError) as e:
            raise APIError(
                resp.status_code,
                "api_error",
                resp.text,
                None,
                resp.headers.get("x-request-id"),
                None,
                resp.content,
            ) from e
        type_ = err.get("type") or "api_error"
        msg = err.get("message") or resp.text
        code = err.get("code")
        rid = resp.headers.get("x-request-id")
        ra = err.get("retry_after")
        if resp.status_code == 429:
            raise RateLimitError(
                resp.status_code, type_, msg, code, rid, ra, resp.content
            )
        raise APIError(resp.status_code, type_, msg, code, rid, ra, resp.content)
