"""Basic authentication implementation for GavaConnect SDK."""

import base64
from dataclasses import dataclass

import httpx


@dataclass(frozen=True, slots=True)
class BasicCredentials:
    """Basic authentication credentials."""

    client_id: str
    client_secret: str


class BasicAuthPolicy:
    """HTTP Basic authentication policy."""

    def __init__(self, creds: BasicCredentials) -> None:
        """Initialize the basic auth policy.

        Args:
            creds: Basic authentication credentials.

        """
        token = base64.b64encode(
            f"{creds.client_id}:{creds.client_secret}".encode()
        ).decode()
        self._header = f"Basic {token}"

    async def authorize(self, request: httpx.Request) -> None:
        """Add basic authentication header to the request.

        Args:
            request: The HTTP request to authorize.

        """
        request.headers["authorization"] = self._header

    async def on_unauthorized(self) -> bool:
        """Handle unauthorized response.

        Returns:
            False, as basic auth cannot refresh credentials.

        """
        return False
