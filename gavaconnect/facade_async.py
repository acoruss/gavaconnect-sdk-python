"""Async facade for GavaConnect SDK."""

from types import TracebackType

from gavaconnect.auth import BasicPair, BasicTokenEndpointProvider, BearerAuthPolicy
from gavaconnect.config import SDKConfig
from gavaconnect.http.transport import AsyncTransport
from gavaconnect.resources.checkers import CheckersClient

__all__ = ["AsyncGavaConnect"]


class AsyncGavaConnect:
    """Async facade for GavaConnect SDK with per-family credentials."""

    def __init__(
        self,
        config: SDKConfig,
        *,
        checkers_client_id: str,
        checkers_client_secret: str,
        token_url: str = "https://sbx.kra.go.ke/v1/token/generate",
    ) -> None:
        """Initialize the async GavaConnect client.

        Args:
            config: SDK configuration.
            checkers_client_id: Client ID for checkers API.
            checkers_client_secret: Client secret for checkers API.
            token_url: Token endpoint URL.

        """
        self._config = config
        self._tr = AsyncTransport(config)
        
        # Setup checkers client with Basic -> Bearer flow
        provider = BasicTokenEndpointProvider(
            token_url=token_url,
            basic=BasicPair(checkers_client_id, checkers_client_secret),
            method="GET",
            early_refresh_s=60,
        )
        self.checkers = CheckersClient(self._tr, BearerAuthPolicy(provider))

    async def __aenter__(self) -> "AsyncGavaConnect":
        """Async context manager entry."""
        return self

    async def __aexit__(
        self, 
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None, 
        exc_tb: TracebackType | None,
    ) -> None:
        """Async context manager exit."""
        await self.close()

    async def close(self) -> None:
        """Close the client and cleanup resources."""
        await self._tr.close()
