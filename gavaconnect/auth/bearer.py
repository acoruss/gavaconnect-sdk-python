"""Bearer token authentication implementation for GavaConnect SDK."""

from __future__ import annotations

from typing import Protocol

import httpx


class AuthPolicy(Protocol):
    """Protocol for authentication policies."""

    async def authorize(self, request: httpx.Request) -> None:
        """Add authentication to the request.

        Args:
            request: The HTTP request to authorize.

        """
        ...

    async def on_unauthorized(self) -> bool:
        """Handle unauthorized response.

        Returns:
            True if authentication was refreshed, False otherwise.

        """
        return False


class TokenProvider(Protocol):
    """Protocol for token providers."""

    async def get_token(self) -> str:
        """Get the current access token.

        Returns:
            The access token.

        """
        ...

    async def refresh(self) -> str:
        """Refresh and return a new access token.

        Returns:
            The new access token.

        """
        ...


class BearerAuthPolicy:
    """Bearer token authentication policy."""

    def __init__(self, provider: TokenProvider) -> None:
        """Initialize the bearer auth policy.

        Args:
            provider: Token provider for obtaining access tokens.

        """
        self._p, self._last = provider, ""

    async def authorize(self, request: httpx.Request) -> None:
        """Add bearer token to the request.

        Args:
            request: The HTTP request to authorize.

        """
        token = await self._p.get_token()
        self._last = token
        request.headers["authorization"] = f"Bearer {token}"

    async def on_unauthorized(self) -> bool:
        """Handle unauthorized response by refreshing the token.

        Returns:
            True if the token was refreshed, False otherwise.

        """
        new_token = await self._p.refresh()
        changed = new_token != self._last
        self._last = new_token
        return changed
