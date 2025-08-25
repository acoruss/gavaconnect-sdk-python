"""Test successful PIN validation."""

import httpx
import pytest
import respx

from gavaconnect.config import SDKConfig
from gavaconnect.facade_async import AsyncGavaConnect


@pytest.mark.asyncio
async def test_checkers_validate_pin_success():
    """Test successful PIN validation with proper response mapping."""
    config = SDKConfig(base_url="https://test.example.com")

    with respx.mock:
        # Mock token endpoint
        token_route = respx.get("https://sbx.kra.go.ke/v1/token/generate").mock(
            return_value=httpx.Response(
                200, json={"access_token": "tok1", "expires_in": 3600}
            )
        )

        # Mock PIN validation endpoint
        pin_route = respx.post("https://test.example.com/checker/v1/pinbypin").mock(
            return_value=httpx.Response(
                200,
                json={
                    "PIN": "A000000000B",
                    "TaxPayerName": "ACME LTD",
                    "status": "VALID",
                    "valid": True,
                },
            )
        )

        async with AsyncGavaConnect(
            config,
            checkers_client_id="test_client",
            checkers_client_secret="test_secret",
        ) as sdk:
            result = await sdk.checkers.validate_pin(pin="A000000000B")

            # Test that fields are properly mapped
            assert result.pin == "A000000000B"
            assert result.taxpayer_name == "ACME LTD"
            assert result.status == "VALID"
            assert result.valid is True

            # Test that model_dump preserves aliases
            dumped = result.model_dump(by_alias=True)
            assert dumped["PIN"] == "A000000000B"
            assert dumped["TaxPayerName"] == "ACME LTD"

            # Verify API calls were made
            assert token_route.called
            assert pin_route.called

            # Verify request content
            pin_request = pin_route.calls[0].request
            assert pin_request.method == "POST"
            assert pin_request.headers["authorization"].startswith("Bearer ")

            # Check JSON payload
            import json

            payload = json.loads(pin_request.content)
            assert payload == {"PIN": "A000000000B"}
