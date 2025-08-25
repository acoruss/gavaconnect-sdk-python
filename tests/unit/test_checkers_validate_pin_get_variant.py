"""Test GET variant of PIN validation."""

import httpx
import pytest
import respx

from gavaconnect.config import SDKConfig
from gavaconnect.facade_async import AsyncGavaConnect


@pytest.mark.asyncio
async def test_checkers_validate_pin_get_variant():
    """Test PIN validation using GET with query parameters."""
    config = SDKConfig(base_url="https://test.example.com")

    with respx.mock:
        # Mock token endpoint
        token_route = respx.get("https://sbx.kra.go.ke/v1/token/generate").mock(
            return_value=httpx.Response(
                200, json={"access_token": "tok1", "expires_in": 3600}
            )
        )

        # Mock PIN validation endpoint with GET
        pin_route = respx.get("https://test.example.com/checker/v1/pinbypin").mock(
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
            result = await sdk.checkers.validate_pin_get(pin="A000000000B")

            # Verify result is correct
            assert result.pin == "A000000000B"
            assert result.taxpayer_name == "ACME LTD"
            assert result.status == "VALID"
            assert result.valid is True

            # Verify calls were made
            assert token_route.called
            assert pin_route.called

            # Verify GET request with query parameters
            pin_request = pin_route.calls[0].request
            assert pin_request.method == "GET"
            assert pin_request.headers["authorization"].startswith("Bearer ")

            # Check query parameters
            assert "PIN=A000000000B" in str(pin_request.url)


@pytest.mark.asyncio
async def test_checkers_validate_pin_get_custom_query_key():
    """Test GET variant with custom query key."""
    config = SDKConfig(base_url="https://test.example.com")

    with respx.mock:
        # Mock token endpoint
        respx.get("https://sbx.kra.go.ke/v1/token/generate").mock(
            return_value=httpx.Response(
                200, json={"access_token": "tok1", "expires_in": 3600}
            )
        )

        # Mock PIN validation endpoint
        pin_route = respx.get("https://test.example.com/checker/v1/pinbypin").mock(
            return_value=httpx.Response(
                200, json={"PIN": "A000000000B", "status": "VALID", "valid": True}
            )
        )

        async with AsyncGavaConnect(
            config,
            checkers_client_id="test_client",
            checkers_client_secret="test_secret",
        ) as sdk:
            await sdk.checkers.validate_pin_get(
                pin="A000000000B", query_key="pin_number"
            )

            # Verify custom query key was used
            pin_request = pin_route.calls[0].request
            assert "pin_number=A000000000B" in str(pin_request.url)
