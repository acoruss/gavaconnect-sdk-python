"""Tests for token provider implementations."""

import asyncio
import time
from unittest.mock import patch

import httpx
import pytest
import respx

from gavaconnect.auth.providers import ClientCredentialsProvider


class TestClientCredentialsProvider:
    """Test ClientCredentialsProvider class."""

    def test_init_minimal(self):
        """Test initialization with minimal parameters."""
        provider = ClientCredentialsProvider(
            token_url="https://auth.example.com/token",
            client_id="test_client",
            client_secret="test_secret"
        )
        
        assert provider._url == "https://auth.example.com/token"
        assert provider._cid == "test_client"
        assert provider._sec == "test_secret"
        assert provider._scope is None
        assert provider._early == 60
        assert isinstance(provider._client, httpx.AsyncClient)
        assert isinstance(provider._lock, asyncio.Lock)
        assert provider._token == ""
        assert provider._exp == 0.0

    def test_init_full_parameters(self):
        """Test initialization with all parameters."""
        custom_client = httpx.AsyncClient()
        provider = ClientCredentialsProvider(
            token_url="https://auth.example.com/token",
            client_id="test_client",
            client_secret="test_secret",
            scope="read write",
            early_refresh_s=120,
            client=custom_client
        )
        
        assert provider._scope == "read write"
        assert provider._early == 120
        assert provider._client is custom_client

    @respx.mock
    @pytest.mark.asyncio
    async def test_fetch_success_without_scope(self):
        """Test successful token fetch without scope."""
        # Mock the token endpoint
        token_route = respx.post("https://auth.example.com/token").mock(
            return_value=httpx.Response(
                200,
                json={
                    "access_token": "test_access_token",
                    "expires_in": 3600
                }
            )
        )
        
        provider = ClientCredentialsProvider(
            token_url="https://auth.example.com/token",
            client_id="test_client",
            client_secret="test_secret"
        )
        
        with patch('time.time', return_value=1000.0):
            token, exp_time = await provider._fetch()
        
        assert token == "test_access_token"
        assert exp_time == 1000.0 + max(30.0, 3600 - 60)  # 4540.0
        
        # Verify the request was made correctly
        assert token_route.called
        request = token_route.calls[0].request
        assert request.method == "POST"
        assert request.url == "https://auth.example.com/token"
        
        # Check the form data
        form_data = dict(httpx.QueryParams(request.content.decode()))
        assert form_data["grant_type"] == "client_credentials"
        assert "scope" not in form_data

    @respx.mock
    @pytest.mark.asyncio
    async def test_fetch_success_with_scope(self):
        """Test successful token fetch with scope."""
        token_route = respx.post("https://auth.example.com/token").mock(
            return_value=httpx.Response(
                200,
                json={
                    "access_token": "scoped_token",
                    "expires_in": 7200
                }
            )
        )
        
        provider = ClientCredentialsProvider(
            token_url="https://auth.example.com/token",
            client_id="test_client",
            client_secret="test_secret",
            scope="read write admin"
        )
        
        await provider._fetch()
        
        # Verify scope was included in request
        assert token_route.called
        request = token_route.calls[0].request
        form_data = dict(httpx.QueryParams(request.content.decode()))
        assert form_data["grant_type"] == "client_credentials"
        assert form_data["scope"] == "read write admin"

    @respx.mock
    @pytest.mark.asyncio
    async def test_fetch_with_custom_expires_in(self):
        """Test fetch with custom expires_in value."""
        respx.post("https://auth.example.com/token").mock(
            return_value=httpx.Response(
                200,
                json={
                    "access_token": "short_lived_token",
                    "expires_in": 300  # 5 minutes
                }
            )
        )
        
        provider = ClientCredentialsProvider(
            token_url="https://auth.example.com/token",
            client_id="test_client",
            client_secret="test_secret",
            early_refresh_s=60
        )
        
        with patch('time.time', return_value=2000.0):
            token, exp_time = await provider._fetch()
        
        # Should use max(30.0, 300 - 60) = 240
        assert exp_time == 2000.0 + 240.0

    @respx.mock
    @pytest.mark.asyncio
    async def test_fetch_without_expires_in(self):
        """Test fetch when response doesn't include expires_in."""
        respx.post("https://auth.example.com/token").mock(
            return_value=httpx.Response(
                200,
                json={
                    "access_token": "default_ttl_token"
                    # No expires_in field
                }
            )
        )
        
        provider = ClientCredentialsProvider(
            token_url="https://auth.example.com/token",
            client_id="test_client",
            client_secret="test_secret"
        )
        
        with patch('time.time', return_value=3000.0):
            token, exp_time = await provider._fetch()
        
        # Should use default 3600 seconds: max(30.0, 3600 - 60) = 3540
        assert exp_time == 3000.0 + 3540.0

    @respx.mock
    @pytest.mark.asyncio
    async def test_fetch_http_error(self):
        """Test fetch when HTTP request fails."""
        respx.post("https://auth.example.com/token").mock(
            return_value=httpx.Response(401, json={"error": "invalid_client"})
        )
        
        provider = ClientCredentialsProvider(
            token_url="https://auth.example.com/token",
            client_id="test_client",
            client_secret="test_secret"
        )
        
        with pytest.raises(httpx.HTTPStatusError):
            await provider._fetch()

    @pytest.mark.asyncio
    async def test_get_token_first_call(self):
        """Test get_token on first call (no cached token)."""
        provider = ClientCredentialsProvider(
            token_url="https://auth.example.com/token",
            client_id="test_client",
            client_secret="test_secret"
        )
        
        # Mock the _fetch method directly for this test
        async def mock_fetch():
            return "fresh_token", 5000.0
        
        provider._fetch = mock_fetch
        
        with patch('time.time', return_value=1000.0):
            token = await provider.get_token()
        
        assert token == "fresh_token"
        assert provider._token == "fresh_token"
        assert provider._exp == 5000.0

    @pytest.mark.asyncio
    async def test_get_token_cached_valid(self):
        """Test get_token with valid cached token."""
        provider = ClientCredentialsProvider(
            token_url="https://auth.example.com/token",
            client_id="test_client",
            client_secret="test_secret"
        )
        
        # Set up cached token
        provider._token = "cached_token"
        provider._exp = 5000.0
        
        # Mock _fetch to track if it's called
        fetch_called = False
        async def mock_fetch():
            nonlocal fetch_called
            fetch_called = True
            return "new_token", 8000.0
        
        provider._fetch = mock_fetch
        
        with patch('time.time', return_value=4000.0):  # Before expiry
            token = await provider.get_token()
        
        assert token == "cached_token"
        assert not fetch_called

    @pytest.mark.asyncio
    async def test_get_token_cached_expired(self):
        """Test get_token with expired cached token."""
        provider = ClientCredentialsProvider(
            token_url="https://auth.example.com/token",
            client_id="test_client",
            client_secret="test_secret"
        )
        
        # Set up expired cached token
        provider._token = "expired_token"
        provider._exp = 4000.0
        
        fetch_called = False
        async def mock_fetch():
            nonlocal fetch_called
            fetch_called = True
            return "new_token", 8000.0
        
        provider._fetch = mock_fetch
        
        with patch('time.time', return_value=5000.0):  # After expiry
            token = await provider.get_token()
        
        assert token == "new_token"
        assert provider._token == "new_token"
        assert provider._exp == 8000.0
        assert fetch_called

    @pytest.mark.asyncio
    async def test_refresh(self):
        """Test refresh method."""
        provider = ClientCredentialsProvider(
            token_url="https://auth.example.com/token",
            client_id="test_client",
            client_secret="test_secret"
        )
        
        # Set up existing token
        provider._token = "old_token"
        provider._exp = 5000.0
        
        fetch_called = False
        async def mock_fetch():
            nonlocal fetch_called
            fetch_called = True
            return "refreshed_token", 8000.0
        
        provider._fetch = mock_fetch
        
        token = await provider.refresh()
        
        assert token == "refreshed_token"
        assert provider._token == "refreshed_token"
        assert provider._exp == 8000.0
        assert fetch_called

    @pytest.mark.asyncio
    async def test_concurrent_get_token_calls(self):
        """Test that concurrent get_token calls are properly synchronized."""
        provider = ClientCredentialsProvider(
            token_url="https://auth.example.com/token",
            client_id="test_client",
            client_secret="test_secret"
        )
        
        fetch_call_count = 0
        
        async def mock_fetch():
            nonlocal fetch_call_count
            fetch_call_count += 1
            await asyncio.sleep(0.1)  # Simulate network delay
            return f"token_{fetch_call_count}", 8000.0
        
        provider._fetch = mock_fetch
        
        with patch('time.time', return_value=1000.0):
            # Make multiple concurrent calls
            tasks = [provider.get_token() for _ in range(5)]
            tokens = await asyncio.gather(*tasks)
        
        # All should get the same token
        assert all(token == "token_1" for token in tokens)
        # _fetch should only be called once due to the lock
        assert fetch_call_count == 1

    @respx.mock
    @pytest.mark.asyncio
    async def test_early_refresh_parameter(self):
        """Test that early_refresh_s parameter affects token expiry calculation."""
        # Mock responses for both providers
        respx.post("https://auth.example.com/token").mock(
            return_value=httpx.Response(
                200,
                json={
                    "access_token": "test_token",
                    "expires_in": 3600
                }
            )
        )
        
        # Test with different early refresh values
        provider1 = ClientCredentialsProvider(
            token_url="https://auth.example.com/token",
            client_id="test_client",
            client_secret="test_secret",
            early_refresh_s=60
        )
        
        provider2 = ClientCredentialsProvider(
            token_url="https://auth.example.com/token",
            client_id="test_client",
            client_secret="test_secret",
            early_refresh_s=300
        )
        
        with patch('time.time', return_value=1000.0):
            _, exp1 = await provider1._fetch()
            _, exp2 = await provider2._fetch()
        
        # Provider1: 1000 + max(30, 3600-60) = 1000 + 3540 = 4540
        # Provider2: 1000 + max(30, 3600-300) = 1000 + 3300 = 4300
        assert exp1 == 4540.0
        assert exp2 == 4300.0

    @respx.mock
    @pytest.mark.asyncio
    async def test_minimum_ttl_enforcement(self):
        """Test that minimum TTL of 30 seconds is enforced."""
        respx.post("https://auth.example.com/token").mock(
            return_value=httpx.Response(
                200,
                json={
                    "access_token": "short_token",
                    "expires_in": 10  # Very short expiry
                }
            )
        )
        
        provider = ClientCredentialsProvider(
            token_url="https://auth.example.com/token",
            client_id="test_client",
            client_secret="test_secret",
            early_refresh_s=60
        )
        
        with patch('time.time', return_value=2000.0):
            _, exp_time = await provider._fetch()
        
        # Should use minimum of 30 seconds: 2000 + max(30, 10-60) = 2000 + 30 = 2030
        assert exp_time == 2030.0

    @respx.mock
    @pytest.mark.asyncio
    async def test_authentication_headers(self):
        """Test that authentication headers are sent correctly."""
        token_route = respx.post("https://auth.example.com/token").mock(
            return_value=httpx.Response(
                200,
                json={
                    "access_token": "test_token",
                    "expires_in": 3600
                }
            )
        )
        
        provider = ClientCredentialsProvider(
            token_url="https://auth.example.com/token",
            client_id="test_client",
            client_secret="test_secret"
        )
        
        await provider._fetch()
        
        # Verify authentication was sent
        assert token_route.called
        request = token_route.calls[0].request
        assert "authorization" in request.headers
        
        # Basic auth should be base64 encoded client_id:client_secret
        import base64
        expected_auth = base64.b64encode(b"test_client:test_secret").decode()
        assert request.headers["authorization"] == f"Basic {expected_auth}"

    @respx.mock
    @pytest.mark.asyncio
    async def test_content_type_header(self):
        """Test that correct content-type header is sent."""
        token_route = respx.post("https://auth.example.com/token").mock(
            return_value=httpx.Response(
                200,
                json={
                    "access_token": "test_token",
                    "expires_in": 3600
                }
            )
        )
        
        provider = ClientCredentialsProvider(
            token_url="https://auth.example.com/token",
            client_id="test_client",
            client_secret="test_secret"
        )
        
        await provider._fetch()
        
        assert token_route.called
        request = token_route.calls[0].request
        assert request.headers["content-type"] == "application/x-www-form-urlencoded"

    @respx.mock
    @pytest.mark.asyncio
    async def test_full_integration_flow(self):
        """Test complete token lifecycle with real HTTP mocking."""
        token_route = respx.post("https://auth.example.com/token").mock(
            return_value=httpx.Response(
                200,
                json={
                    "access_token": "integration_token",
                    "expires_in": 3600
                }
            )
        )
        
        provider = ClientCredentialsProvider(
            token_url="https://auth.example.com/token",
            client_id="integration_client",
            client_secret="integration_secret",
            scope="read write"
        )
        
        with patch('time.time', return_value=1000.0):
            # First call should fetch token
            token1 = await provider.get_token()
            assert token1 == "integration_token"
            assert token_route.call_count == 1
            
            # Second call should use cached token
            token2 = await provider.get_token()
            assert token2 == "integration_token"
            assert token_route.call_count == 1  # No additional calls
            
            # Refresh should force new fetch
            token3 = await provider.refresh()
            assert token3 == "integration_token"
            assert token_route.call_count == 2  # One additional call
