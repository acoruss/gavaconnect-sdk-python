"""HTTP transport implementation with retry logic and error handling."""

from __future__ import annotations

import asyncio
import random
from collections.abc import Awaitable, Callable
from typing import Any

import httpx

from gavaconnect.auth import AuthPolicy
from gavaconnect.config import SDKConfig
from gavaconnect.errors import APIError, RateLimitError, TransportError
from gavaconnect.helpers.idempotency import _can_retry, _full_jitter, _parse_retry_after

RequestHook = Callable[[httpx.Request], Awaitable[None]]
ResponseHook = Callable[[httpx.Request, httpx.Response], Awaitable[None]]
_rng = random.SystemRandom()


class AsyncTransport:
    """Shared HTTP transport with advanced features.

    Features include:
    - request/response middleware hooks
    - timeouts (connect/read/total)
    - bounded retries with exponential full jitter (honors Retry-After)
    - single 401 → auth.on_unauthorized() → retry once
    """

    def __init__(
        self,
        cfg: SDKConfig,
        *,
        on_request: list[RequestHook] | None = None,
        on_response: list[ResponseHook] | None = None,
    ) -> None:
        """Initialize the async transport.

        Args:
            cfg: SDK configuration object
            on_request: Optional list of request hooks
            on_response: Optional list of response hooks

        """
        self.cfg = cfg
        self._on_request = on_request or []
        self._on_response = on_response or []
        self.client = httpx.AsyncClient(
            base_url=cfg.base_url,
            http2=True,
            headers={"user-agent": cfg.user_agent, "x-client-version": cfg.user_agent},
            timeout=httpx.Timeout(
                cfg.total_timeout_s,
                connect=cfg.connect_timeout_s,
                read=cfg.read_timeout_s,
            ),
        )

    async def close(self) -> None:
        """Close the HTTP client connection."""
        await self.client.aclose()

    async def request(
        self,
        method: str,
        url: str,
        *,
        auth: AuthPolicy | None = None,
        **kw: Any,  # noqa: ANN401
    ) -> httpx.Response:
        """Build and send a request.

        NOTE: if you pass a streaming body, disable retries or ensure it's repeatable.

        Args:
            method: HTTP method
            url: Request URL
            auth: Optional auth policy
            **kw: Additional keyword arguments for the request

        Returns:
            The HTTP response

        """
        attempt = 1
        did_refresh = False

        # Always rebuild the request each loop to avoid reusing consumed bodies.
        def build() -> httpx.Request:
            req = self.client.build_request(method, url, **kw)
            req.extensions["attempt"] = attempt
            return req

        req = build()
        if auth:
            await auth.authorize(req)
        for req_hook in self._on_request:
            try:
                await req_hook(req)
            except Exception:
                # Hooks must not break transport; swallow but continue.
                pass

        while True:
            try:
                resp = await self.client.send(req, stream=False)
            except httpx.HTTPError as e:
                # Network/protocol error
                if attempt > self.cfg.retry.max_attempts or not _can_retry(method, req):
                    raise TransportError(str(e)) from e
                delay = _full_jitter(
                    self.cfg.retry.base_backoff_s, attempt, self.cfg.retry.max_cap_s
                )
                await asyncio.sleep(delay)
                attempt += 1
                req = build()
                if auth:
                    await auth.authorize(req)
                continue

            # Run response hooks (even if we'll retry) so logs/metrics capture all attempts.
            for resp_hook in self._on_response:
                try:
                    await resp_hook(req, resp)
                except Exception:
                    pass

            # 401 handling: give auth one chance to refresh and retry once.
            if resp.status_code == 401 and auth and not did_refresh:
                try:
                    refreshed = await auth.on_unauthorized()
                except Exception:
                    refreshed = False
                if refreshed:
                    did_refresh = True
                    attempt += 1
                    req = build()
                    await auth.authorize(req)
                    # Optional: re-run request hooks for the retried request
                    for req_hook in self._on_request:
                        try:
                            await req_hook(req)
                        except Exception:
                            pass
                    continue  # retry now with refreshed auth

            # Regular retry policy for 429/5xx (and any configured statuses)
            should_retry_status = resp.status_code in self.cfg.retry.retry_on_status
            if (
                should_retry_status
                and attempt <= self.cfg.retry.max_attempts
                and _can_retry(method, req)
            ):
                ra = _parse_retry_after(resp.headers.get("retry-after"))
                delay = (
                    ra
                    if ra is not None
                    else _full_jitter(
                        self.cfg.retry.base_backoff_s, attempt, self.cfg.retry.max_cap_s
                    )
                )
                # Small +/-10% wiggle around server hint to avoid alignment
                if ra is not None:
                    wiggle = ra * 0.1
                    delay = max(0.0, _rng.uniform(max(0.0, ra - wiggle), ra + wiggle))
                await asyncio.sleep(delay)
                attempt += 1
                req = build()
                if auth:
                    await auth.authorize(req)
                # Optional: re-run request hooks for the retried request
                for req_hook in self._on_request:
                    try:
                        await req_hook(req)
                    except Exception:
                        pass
                continue

            # Done (either success or non-retryable error)
            return resp

    # Optional helper if you standardize error envelopes in your SDK.
    @staticmethod
    def raise_for_api_error(resp: httpx.Response) -> None:
        """Raise appropriate API error based on response status and content.

        Args:
            resp: The HTTP response to check for errors

        Raises:
            APIError: For general API errors
            RateLimitError: For rate limit errors (429 status)

        """
        if resp.status_code < 400:
            return
        try:
            body = resp.json()
            err = body.get("error", {})
        except Exception:
            raise APIError(
                resp.status_code,
                "api_error",
                resp.text,
                None,
                resp.headers.get("x-request-id"),
                None,
                resp.content,
            ) from None
        typ = err.get("type") or "api_error"
        msg = err.get("message") or resp.text
        code = err.get("code")
        rid = resp.headers.get("x-request-id")
        ra = err.get("retry_after")
        if resp.status_code == 429:
            raise RateLimitError(
                resp.status_code, typ, msg, code, rid, ra, resp.content
            )
        raise APIError(resp.status_code, typ, msg, code, rid, ra, resp.content)
