"""Token provider implementations for GavaConnect SDK."""

import asyncio
import time
from typing import Literal

import httpx

from .credentials import BasicPair

# Minimum token TTL to prevent rapid refresh cycles
MIN_TOKEN_TTL_S = 30.0


class ClientCredentialsProvider:
    """OAuth2 client credentials token provider."""

    def __init__(
        self,
        token_url: str,
        client_id: str,
        client_secret: str,
        scope: str | None = None,
        early_refresh_s: int = 60,
        client: httpx.AsyncClient | None = None,
        token_timeout_s: float = 10.0,
    ) -> None:
        """Initialize the client credentials provider.

        Args:
            token_url: OAuth2 token endpoint URL.
            client_id: OAuth2 client ID.
            client_secret: OAuth2 client secret.
            scope: Optional scope for the token.
            early_refresh_s: Seconds before expiry to refresh token.
            client: Optional HTTP client to use.
            token_timeout_s: Timeout for token requests in seconds.

        """
        self._url, self._cid, self._sec, self._scope = (
            token_url,
            client_id,
            client_secret,
            scope,
        )
        self._early, self._client = (
            early_refresh_s,
            (client or httpx.AsyncClient(timeout=token_timeout_s)),
        )
        self._lock = asyncio.Lock()
        # Security note: tokens stored in memory - consider using keyring for production
        self._token, self._exp = "", 0.0

    async def _fetch(self) -> tuple[str, float]:
        data = {"grant_type": "client_credentials"} | (
            {"scope": self._scope} if self._scope else {}
        )
        r = await self._client.post(
            self._url,
            auth=(self._cid, self._sec),
            data=data,
            headers={"content-type": "application/x-www-form-urlencoded"},
        )
        r.raise_for_status()
        p = r.json()
        ttl = float(p.get("expires_in", 3600))
        return p["access_token"], time.time() + max(MIN_TOKEN_TTL_S, ttl - self._early)

    async def get_token(self) -> str:
        """Get the current access token, refreshing if necessary.

        Returns:
            The access token.

        """
        async with self._lock:
            if self._token and time.time() < self._exp:
                return self._token
            self._token, self._exp = await self._fetch()
            return self._token

    async def refresh(self) -> str:
        """Force refresh the access token.

        Returns:
            The new access token.

        """
        async with self._lock:
            self._token, self._exp = await self._fetch()
            return self._token


class BasicTokenEndpointProvider:
    """Token provider using HTTP Basic auth against a token endpoint."""

    def __init__(
        self,
        token_url: str,
        basic: BasicPair,
        method: Literal["GET", "POST"] = "POST",
        early_refresh_s: int = 60,
        client: httpx.AsyncClient | None = None,
        token_timeout_s: float = 10.0,
    ) -> None:
        """Initialize the basic token endpoint provider.

        Args:
            token_url: Token endpoint URL.
            basic: Basic auth credentials.
            method: HTTP method to use (GET or POST).
            early_refresh_s: Seconds before expiry to refresh token.
            client: Optional HTTP client to use.
            token_timeout_s: Timeout for token requests in seconds.

        """
        self._url = token_url
        self._basic = basic
        self._method = method
        self._early = early_refresh_s
        self._client = client or httpx.AsyncClient(timeout=token_timeout_s)
        self._lock = asyncio.Lock()
        # Security note: tokens stored in memory - consider using keyring for production
        self._token, self._exp = "", 0.0

    async def _fetch(self) -> tuple[str, float]:
        """Fetch a new token from the endpoint."""
        auth = (self._basic.client_id, self._basic.client_secret)
        
        if self._method == "GET":
            resp = await self._client.get(self._url, auth=auth)
        else:
            resp = await self._client.post(self._url, auth=auth)
            
        resp.raise_for_status()
        payload = resp.json()
        ttl = float(payload.get("expires_in", 3600))
        return payload["access_token"], time.time() + max(MIN_TOKEN_TTL_S, ttl - self._early)

    async def get_token(self) -> str:
        """Get the current access token, refreshing if necessary.

        Returns:
            The access token.

        """
        async with self._lock:
            if self._token and time.time() < self._exp:
                return self._token
            self._token, self._exp = await self._fetch()
            return self._token

    async def refresh(self) -> str:
        """Force refresh the access token.

        Returns:
            The new access token.

        """
        async with self._lock:
            self._token, self._exp = await self._fetch()
            return self._token
