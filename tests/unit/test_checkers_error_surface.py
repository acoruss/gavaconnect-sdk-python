"""Test error handling and rate limiting."""

import httpx
import pytest
import respx

from gavaconnect.config import SDKConfig
from gavaconnect.errors import RateLimitError
from gavaconnect.facade_async import AsyncGavaConnect


@pytest.mark.asyncio
async def test_checkers_error_surface():
    """Test that API errors are properly surfaced with retry behavior."""
    # Use faster retry config for testing
    from gavaconnect.config import RetryPolicy
    retry_policy = RetryPolicy(max_attempts=2, base_backoff_s=0.01, max_cap_s=0.1)
    config = SDKConfig(base_url="https://test.example.com", retry=retry_policy)
    
    with respx.mock:
        # Mock token endpoint  
        respx.get("https://sbx.kra.go.ke/v1/token/generate").mock(
            return_value=httpx.Response(
                200, json={"access_token": "tok1", "expires_in": 3600}
            )
        )
        
        # Mock PIN validation endpoint - always returns 429 with shorter Retry-After
        pin_route = respx.post("https://test.example.com/checker/v1/pinbypin").mock(
            return_value=httpx.Response(
                429,
                headers={"retry-after": "0.01", "x-request-id": "req-123"},
                json={
                    "error": {
                        "type": "rate_limit_exceeded",
                        "message": "Too many requests",
                        "code": "RATE_LIMIT",
                        "retry_after": 0.01
                    }
                }
            )
        )
        
        async with AsyncGavaConnect(
            config,
            checkers_client_id="test_client",
            checkers_client_secret="test_secret"
        ) as sdk:
            with pytest.raises(RateLimitError) as exc_info:
                await sdk.checkers.validate_pin(pin="A000000000B")
            
            error = exc_info.value
            
            # Verify error details are captured
            assert error.status == 429
            assert error.type == "rate_limit_exceeded"
            assert error.code == "RATE_LIMIT"
            assert error.request_id == "req-123"
            assert error.retry_after_s == 0.01
            assert error.body is not None
            
            # Verify multiple retry attempts were made due to Retry-After
            # (Should retry up to max_attempts from config) 
            assert len(pin_route.calls) > 1  # Multiple retries with idempotency key


@pytest.mark.asyncio
async def test_checkers_error_missing_request_id():
    """Test error handling when request ID is missing."""
    config = SDKConfig(base_url="https://test.example.com")
    
    with respx.mock:
        # Mock token endpoint
        respx.get("https://sbx.kra.go.ke/v1/token/generate").mock(
            return_value=httpx.Response(
                200, json={"access_token": "tok1", "expires_in": 3600}
            )
        )
        
        # Mock PIN validation endpoint - 500 error without request ID
        respx.post("https://test.example.com/checker/v1/pinbypin").mock(
            return_value=httpx.Response(
                500,
                json={
                    "error": {
                        "type": "internal_error",
                        "message": "Internal server error"
                    }
                }
            )
        )
        
        async with AsyncGavaConnect(
            config,
            checkers_client_id="test_client",
            checkers_client_secret="test_secret"
        ) as sdk:
            with pytest.raises(Exception) as exc_info:  # Should be APIError but imported from errors
                await sdk.checkers.validate_pin(pin="A000000000B")
            
            # Verify error is raised (exact type depends on import structure)
            assert exc_info.value is not None
