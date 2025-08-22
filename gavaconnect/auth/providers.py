"""Token provider implementations for GavaConnect SDK."""

import asyncio
import time

import httpx

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
