"""Test 401 handling with auth refresh."""

import httpx
import pytest
import respx

from gavaconnect.config import SDKConfig
from gavaconnect.facade_async import AsyncGavaConnect


@pytest.mark.asyncio
async def test_checkers_validate_pin_401_then_refresh():
    """Test 401 response triggers auth refresh and retry."""
    config = SDKConfig(base_url="https://test.example.com")
    
    with respx.mock:
        # Mock token endpoint - returns different tokens on subsequent calls
        token_responses = [
            httpx.Response(200, json={"access_token": "tokA", "expires_in": 3600}),
            httpx.Response(200, json={"access_token": "tokB", "expires_in": 3600}),
        ]
        token_route = respx.get("https://sbx.kra.go.ke/v1/token/generate").mock(
            side_effect=token_responses
        )
        
        # Mock PIN validation endpoint - 401 first, then success
        pin_responses = [
            httpx.Response(401, json={"error": {"type": "unauthorized", "message": "Invalid token"}}),
            httpx.Response(200, json={
                "PIN": "A000000000B",
                "TaxPayerName": "ACME LTD", 
                "status": "VALID",
                "valid": True
            })
        ]
        pin_route = respx.post("https://test.example.com/checker/v1/pinbypin").mock(
            side_effect=pin_responses
        )
        
        async with AsyncGavaConnect(
            config,
            checkers_client_id="test_client",
            checkers_client_secret="test_secret"
        ) as sdk:
            result = await sdk.checkers.validate_pin(pin="A000000000B")
            
            # Should eventually succeed after retry
            assert result.pin == "A000000000B"
            assert result.valid is True
            
            # Verify token endpoint called twice (initial + refresh)
            assert len(token_route.calls) == 2
            
            # Verify PIN endpoint called twice (401 + retry)
            assert len(pin_route.calls) == 2
            
            # Verify second request used new token
            first_auth = pin_route.calls[0].request.headers["authorization"]
            second_auth = pin_route.calls[1].request.headers["authorization"]
            assert first_auth.startswith("Bearer tokA")
            assert second_auth.startswith("Bearer tokB")
            assert first_auth != second_auth
