"""PIN validation client for KRA checkers."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from gavaconnect.auth.bearer import BearerAuthPolicy
from gavaconnect.helpers.idempotency import idempotency_headers
from gavaconnect.http.transport import AsyncTransport


class PinCheckResult(BaseModel):
    """Result of PIN validation check."""

    pin: str | None = Field(default=None, alias="PIN")
    taxpayer_name: str | None = Field(default=None, alias="TaxPayerName")
    status: str | None = None
    valid: bool | None = None

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class CheckersClient:
    """Client for KRA PIN validation endpoints."""

    def __init__(self, tr: AsyncTransport, auth: BearerAuthPolicy) -> None:
        """Initialize the checkers client.

        Args:
            tr: Transport instance for HTTP requests.
            auth: Bearer authentication policy.

        """
        self._tr = tr
        self._auth = auth

    async def validate_pin(self, *, pin: str, pin_key: str = "PIN") -> PinCheckResult:
        """Validate a KRA PIN using POST with JSON payload.

        Args:
            pin: The PIN to validate.
            pin_key: The JSON key name for the PIN field.

        Returns:
            PIN validation result.

        """
        payload = {pin_key: pin}
        return await self.validate_pin_raw(payload)

    async def validate_pin_get(
        self, *, pin: str, query_key: str = "PIN"
    ) -> PinCheckResult:
        """Validate a KRA PIN using GET with query parameters.

        Args:
            pin: The PIN to validate.
            query_key: The query parameter name for the PIN field.

        Returns:
            PIN validation result.

        """
        resp = await self._tr.request(
            "GET",
            "/checker/v1/pinbypin",
            auth=self._auth,
            params={query_key: pin},
        )
        self._tr.raise_for_api_error(resp)
        return PinCheckResult.model_validate(resp.json())

    async def validate_pin_raw(self, payload: dict[str, Any]) -> PinCheckResult:
        """Validate a PIN using raw payload.

        Args:
            payload: Raw JSON payload to send.

        Returns:
            PIN validation result.

        """
        headers = idempotency_headers()  # Make POST requests retryable
        resp = await self._tr.request(
            "POST",
            "/checker/v1/pinbypin",
            auth=self._auth,
            json=payload,
            headers=headers,
        )
        self._tr.raise_for_api_error(resp)
        return PinCheckResult.model_validate(resp.json())
