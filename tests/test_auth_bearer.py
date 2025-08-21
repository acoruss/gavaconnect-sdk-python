"""Tests for bearer authentication module."""

from unittest.mock import AsyncMock, Mock

import httpx
import pytest
import respx

from gavaconnect.auth.bearer import BearerAuthPolicy
from gavaconnect.auth.providers import ClientCredentialsProvider


class MockTokenProvider:
    """Mock token provider for testing."""

    def __init__(
        self, token: str = "test_token", refresh_token: str = "new_token"
    ) -> None:
        """Initialize the mock token provider.

        Args:
            token: The initial token to return.
            refresh_token: The token to return after refresh.

        """
        self.token = token
        self.refresh_token = refresh_token
        self.get_token_calls = 0
        self.refresh_calls = 0

    async def get_token(self) -> str:
        """Mock get_token method."""
        self.get_token_calls += 1
        return self.token

    async def refresh(self) -> str:
        """Mock refresh method."""
        self.refresh_calls += 1
        self.token = self.refresh_token
        return self.refresh_token


class TestBearerAuthPolicy:
    """Test BearerAuthPolicy class."""

    def test_init(self):
        """Test BearerAuthPolicy initialization."""
        provider = MockTokenProvider()
        policy = BearerAuthPolicy(provider)

        assert policy._p is provider
        assert policy._last == ""

    @pytest.mark.asyncio
    async def test_authorize(self):
        """Test authorization of a request."""
        provider = MockTokenProvider(token="test_access_token")
        policy = BearerAuthPolicy(provider)

        request = httpx.Request("GET", "https://example.com")
        await policy.authorize(request)

        assert request.headers["authorization"] == "Bearer test_access_token"
        assert policy._last == "test_access_token"
        assert provider.get_token_calls == 1

    @pytest.mark.asyncio
    async def test_authorize_multiple_calls(self):
        """Test multiple authorization calls."""
        provider = MockTokenProvider(token="token123")
        policy = BearerAuthPolicy(provider)

        request1 = httpx.Request("GET", "https://example.com/1")
        request2 = httpx.Request("GET", "https://example.com/2")

        await policy.authorize(request1)
        await policy.authorize(request2)

        assert request1.headers["authorization"] == "Bearer token123"
        assert request2.headers["authorization"] == "Bearer token123"
        assert provider.get_token_calls == 2

    @pytest.mark.asyncio
    async def test_on_unauthorized_token_changed(self):
        """Test unauthorized handling when token changes."""
        provider = MockTokenProvider(token="old_token", refresh_token="new_token")
        policy = BearerAuthPolicy(provider)

        # Set initial token
        policy._last = "old_token"

        result = await policy.on_unauthorized()

        assert result is True  # Token changed
        assert policy._last == "new_token"
        assert provider.refresh_calls == 1

    @pytest.mark.asyncio
    async def test_on_unauthorized_token_unchanged(self):
        """Test unauthorized handling when token doesn't change."""
        provider = MockTokenProvider(token="same_token", refresh_token="same_token")
        policy = BearerAuthPolicy(provider)

        # Set initial token to same as refresh token
        policy._last = "same_token"

        result = await policy.on_unauthorized()

        assert result is False  # Token didn't change
        assert policy._last == "same_token"
        assert provider.refresh_calls == 1

    @pytest.mark.asyncio
    async def test_on_unauthorized_empty_last_token(self):
        """Test unauthorized handling with empty last token."""
        provider = MockTokenProvider(refresh_token="new_token")
        policy = BearerAuthPolicy(provider)

        # _last starts as empty string
        result = await policy.on_unauthorized()

        assert result is True  # Empty string != "new_token"
        assert policy._last == "new_token"

    @pytest.mark.asyncio
    async def test_full_flow(self):
        """Test complete authorization and refresh flow."""
        provider = MockTokenProvider(
            token="initial_token", refresh_token="refreshed_token"
        )
        policy = BearerAuthPolicy(provider)

        # Initial authorization
        request = httpx.Request("GET", "https://example.com")
        await policy.authorize(request)
        assert request.headers["authorization"] == "Bearer initial_token"

        # Unauthorized response triggers refresh
        changed = await policy.on_unauthorized()
        assert changed is True
        assert policy._last == "refreshed_token"

        # New authorization uses refreshed token
        request2 = httpx.Request("GET", "https://example.com/2")
        await policy.authorize(request2)
        assert request2.headers["authorization"] == "Bearer refreshed_token"


class TestTokenProviderProtocol:
    """Test TokenProvider protocol compliance."""

    @pytest.mark.asyncio
    async def test_mock_provider_compliance(self):
        """Test that mock provider implements the protocol correctly."""
        provider = MockTokenProvider()

        # Should have async get_token and refresh methods
        token = await provider.get_token()
        assert isinstance(token, str)

        refresh_token = await provider.refresh()
        assert isinstance(refresh_token, str)

    @pytest.mark.asyncio
    async def test_provider_with_async_mock(self):
        """Test using AsyncMock for token provider."""
        provider = Mock()
        provider.get_token = AsyncMock(return_value="mocked_token")
        provider.refresh = AsyncMock(return_value="mocked_refresh")

        policy = BearerAuthPolicy(provider)

        request = httpx.Request("GET", "https://example.com")
        await policy.authorize(request)

        assert request.headers["authorization"] == "Bearer mocked_token"
        provider.get_token.assert_called_once()

        result = await policy.on_unauthorized()
        assert result is True  # "" != "mocked_refresh"
        provider.refresh.assert_called_once()


class TestBearerAuthPolicyIntegration:
    """Integration tests for BearerAuthPolicy with real token providers."""

    @respx.mock
    @pytest.mark.asyncio
    async def test_integration_with_client_credentials_provider(self):
        """Test BearerAuthPolicy with ClientCredentialsProvider using real HTTP mocking."""
        # Mock the OAuth2 token endpoint
        token_route = respx.post("https://auth.example.com/oauth/token").mock(
            return_value=httpx.Response(
                200,
                json={
                    "access_token": "real_integration_token",
                    "expires_in": 3600,
                    "token_type": "Bearer",
                },
            )
        )

        # Create a real ClientCredentialsProvider
        provider = ClientCredentialsProvider(
            token_url="https://auth.example.com/oauth/token",
            client_id="integration_client",
            client_secret="integration_secret",
            scope="api:read api:write",
        )

        # Create BearerAuthPolicy with the real provider
        auth_policy = BearerAuthPolicy(provider)

        # Test authorization
        request = httpx.Request("GET", "https://api.example.com/data")
        await auth_policy.authorize(request)

        # Verify the request was authorized correctly
        assert request.headers["authorization"] == "Bearer real_integration_token"
        assert token_route.called

        # Verify the OAuth request was made correctly
        oauth_request = token_route.calls[0].request
        assert oauth_request.method == "POST"
        form_data = dict(httpx.QueryParams(oauth_request.content.decode()))
        assert form_data["grant_type"] == "client_credentials"
        assert form_data["scope"] == "api:read api:write"

    @respx.mock
    @pytest.mark.asyncio
    async def test_integration_refresh_flow(self):
        """Test complete refresh flow with real HTTP mocking."""
        call_count = 0

        def token_response(request: httpx.Request) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            return httpx.Response(
                200, json={"access_token": f"token_v{call_count}", "expires_in": 3600}
            )

        # Mock endpoint that returns different tokens
        token_route = respx.post("https://auth.example.com/oauth/token").mock(
            side_effect=token_response
        )

        provider = ClientCredentialsProvider(
            token_url="https://auth.example.com/oauth/token",
            client_id="refresh_client",
            client_secret="refresh_secret",
        )

        auth_policy = BearerAuthPolicy(provider)

        # First authorization
        request1 = httpx.Request("GET", "https://api.example.com/resource1")
        await auth_policy.authorize(request1)
        assert request1.headers["authorization"] == "Bearer token_v1"
        assert token_route.call_count == 1

        # Simulate unauthorized response and refresh
        changed = await auth_policy.on_unauthorized()
        assert changed is True  # Token should have changed
        assert token_route.call_count == 2

        # New authorization should use refreshed token (cached)
        request2 = httpx.Request("GET", "https://api.example.com/resource2")
        await auth_policy.authorize(request2)
        assert (
            request2.headers["authorization"] == "Bearer token_v2"
        )  # Uses cached refreshed token
        # Should still be 2 calls since token is cached
        assert token_route.call_count == 2

    @respx.mock
    @pytest.mark.asyncio
    async def test_integration_error_handling(self):
        """Test error handling in integration scenario."""
        # Mock OAuth endpoint that returns an error
        respx.post("https://auth.example.com/oauth/token").mock(
            return_value=httpx.Response(
                401,
                json={
                    "error": "invalid_client",
                    "error_description": "Client authentication failed",
                },
            )
        )

        provider = ClientCredentialsProvider(
            token_url="https://auth.example.com/oauth/token",
            client_id="invalid_client",
            client_secret="invalid_secret",
        )

        auth_policy = BearerAuthPolicy(provider)

        # Authorization should fail with HTTP error
        request = httpx.Request("GET", "https://api.example.com/protected")

        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            await auth_policy.authorize(request)

        assert exc_info.value.response.status_code == 401

    @respx.mock
    @pytest.mark.asyncio
    async def test_integration_caching_behavior(self):
        """Test that token caching works correctly in integration."""
        token_route = respx.post("https://auth.example.com/oauth/token").mock(
            return_value=httpx.Response(
                200, json={"access_token": "cached_token", "expires_in": 3600}
            )
        )

        provider = ClientCredentialsProvider(
            token_url="https://auth.example.com/oauth/token",
            client_id="cache_client",
            client_secret="cache_secret",
        )

        auth_policy = BearerAuthPolicy(provider)

        # Multiple authorizations should use cached token
        for i in range(3):
            request = httpx.Request("GET", f"https://api.example.com/endpoint{i}")
            await auth_policy.authorize(request)
            assert request.headers["authorization"] == "Bearer cached_token"

        # Only first call should hit the token endpoint (due to caching)
        assert token_route.call_count == 1
