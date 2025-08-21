"""Tests for HTTP transport layer."""

import asyncio
import json
from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest

from gavaconnect.auth import AuthPolicy
from gavaconnect.config import RetryPolicy, SDKConfig
from gavaconnect.errors import APIError, RateLimitError, TransportError
from gavaconnect.http.transport import AsyncTransport, _jitter


class TestJitter:
    """Test the _jitter function."""

    def test_jitter_calculation(self):
        """Test jitter calculation with different inputs."""
        # Test with base=1.0, attempt=1
        result = _jitter(1.0, 1)
        # Should be base * (2^0) * (1 + random * 0.2) = 1.0 * 1 * (1.0 to 1.2)
        assert 1.0 <= result <= 1.2
        
        # Test with base=0.5, attempt=2
        result = _jitter(0.5, 2)
        # Should be 0.5 * (2^1) * (1.0 to 1.2) = 1.0 to 1.2
        assert 1.0 <= result <= 1.2
        
        # Test with base=0.2, attempt=3
        result = _jitter(0.2, 3)
        # Should be 0.2 * (2^2) * (1.0 to 1.2) = 0.8 to 0.96
        assert 0.8 <= result <= 0.96

    def test_jitter_randomness(self):
        """Test that jitter produces different results."""
        results = [_jitter(1.0, 1) for _ in range(10)]
        # Results should not all be the same (very unlikely)
        assert len(set(results)) > 1


class TestAsyncTransport:
    """Test AsyncTransport class."""

    def test_init(self):
        """Test AsyncTransport initialization."""
        config = SDKConfig(
            base_url="https://api.example.com",
            connect_timeout_s=10.0,
            read_timeout_s=60.0,
            total_timeout_s=70.0,
            user_agent="test-agent/1.0.0"
        )
        
        transport = AsyncTransport(config)
        
        assert transport.cfg == config
        assert isinstance(transport.client, httpx.AsyncClient)
        assert str(transport.client.base_url).rstrip("/") == "https://api.example.com"

    @pytest.mark.asyncio
    async def test_close(self):
        """Test transport close method."""
        config = SDKConfig(base_url="https://api.example.com")
        transport = AsyncTransport(config)
        
        # Test that close works without error
        await transport.close()

    @pytest.mark.asyncio
    async def test_successful_request(self):
        """Test successful HTTP request."""
        config = SDKConfig(base_url="https://api.example.com")
        transport = AsyncTransport(config)
        
        # Mock the client methods
        mock_request = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        
        with patch.object(transport.client, 'build_request', return_value=mock_request), \
             patch.object(transport.client, 'send', new_callable=AsyncMock, return_value=mock_response):
            
            result = await transport.request("GET", "/test")
            
            assert result == mock_response
            transport.client.build_request.assert_called_once_with("GET", "/test")
            transport.client.send.assert_called_once_with(mock_request, stream=False)
        
        await transport.close()

    @pytest.mark.asyncio
    async def test_request_with_auth(self):
        """Test request with authentication."""
        config = SDKConfig(base_url="https://api.example.com")
        transport = AsyncTransport(config)
        
        # Mock auth policy
        auth = Mock(spec=AuthPolicy)
        auth.authorize = AsyncMock()
        auth.on_unauthorized = AsyncMock(return_value=False)
        
        # Mock the client methods
        mock_request = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        
        with patch.object(transport.client, 'build_request', return_value=mock_request), \
             patch.object(transport.client, 'send', new_callable=AsyncMock, return_value=mock_response):
            
            result = await transport.request("POST", "/test", auth=auth, json={"data": "test"})
            
            assert result == mock_response
            auth.authorize.assert_called_once_with(mock_request)
        
        await transport.close()

    @pytest.mark.asyncio
    async def test_request_with_401_and_retry(self):
        """Test request handling 401 with auth retry."""
        config = SDKConfig(base_url="https://api.example.com")
        transport = AsyncTransport(config)
        
        # Mock auth policy
        auth = Mock(spec=AuthPolicy)
        auth.authorize = AsyncMock()
        auth.on_unauthorized = AsyncMock(return_value=True)  # Retry auth
        
        # Mock responses: first 401, then 200
        mock_request = Mock()
        mock_response_401 = Mock()
        mock_response_401.status_code = 401
        mock_response_200 = Mock()
        mock_response_200.status_code = 200
        
        with patch.object(transport.client, 'build_request', return_value=mock_request), \
             patch.object(transport.client, 'send', new_callable=AsyncMock, side_effect=[mock_response_401, mock_response_200]):
            
            result = await transport.request("GET", "/test", auth=auth)
            
            assert result == mock_response_200
            # Auth should be called twice (initial and retry)
            assert auth.authorize.call_count == 2
            auth.on_unauthorized.assert_called_once()
        
        await transport.close()

    @pytest.mark.asyncio
    async def test_request_with_http_error_retry(self):
        """Test request retry on HTTP errors."""
        config = SDKConfig(
            base_url="https://api.example.com",
            retry=RetryPolicy(max_attempts=2, base_backoff_s=0.01)  # Fast retry for testing
        )
        transport = AsyncTransport(config)
        
        mock_request = Mock()
        http_error = httpx.ConnectError("Connection failed")
        mock_response = Mock()
        mock_response.status_code = 200
        
        with patch.object(transport.client, 'build_request', return_value=mock_request), \
             patch.object(transport.client, 'send', new_callable=AsyncMock, side_effect=[http_error, mock_response]), \
             patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
            
            result = await transport.request("GET", "/test")
            
            assert result == mock_response
            mock_sleep.assert_called_once()  # Should have slept once for retry
        
        await transport.close()

    @pytest.mark.asyncio
    async def test_request_max_retries_exceeded(self):
        """Test request fails after max retries."""
        config = SDKConfig(
            base_url="https://api.example.com",
            retry=RetryPolicy(max_attempts=2, base_backoff_s=0.01)
        )
        transport = AsyncTransport(config)
        
        mock_request = Mock()
        http_error = httpx.ConnectError("Connection failed")
        
        with patch.object(transport.client, 'build_request', return_value=mock_request), \
             patch.object(transport.client, 'send', new_callable=AsyncMock, side_effect=http_error), \
             pytest.raises(TransportError, match="Connection failed"):
            
            await transport.request("GET", "/test")
        
        await transport.close()

    @pytest.mark.asyncio
    async def test_request_with_status_code_retry(self):
        """Test request retry on specific status codes."""
        config = SDKConfig(
            base_url="https://api.example.com",
            retry=RetryPolicy(max_attempts=2, base_backoff_s=0.01, retry_on_status=(503,))
        )
        transport = AsyncTransport(config)
        
        mock_request = Mock()
        mock_response_503 = Mock()
        mock_response_503.status_code = 503
        mock_response_503.headers = {}
        mock_response_200 = Mock()
        mock_response_200.status_code = 200
        
        with patch.object(transport.client, 'build_request', return_value=mock_request), \
             patch.object(transport.client, 'send', new_callable=AsyncMock, side_effect=[mock_response_503, mock_response_200]), \
             patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
            
            result = await transport.request("GET", "/test")
            
            assert result == mock_response_200
            mock_sleep.assert_called_once()
        
        await transport.close()

    @pytest.mark.asyncio
    async def test_request_with_retry_after_header(self):
        """Test request respects retry-after header."""
        config = SDKConfig(
            base_url="https://api.example.com",
            retry=RetryPolicy(max_attempts=2, retry_on_status=(429,))
        )
        transport = AsyncTransport(config)
        
        mock_request = Mock()
        mock_response_429 = Mock()
        mock_response_429.status_code = 429
        mock_response_429.headers = {"retry-after": "2"}
        mock_response_200 = Mock()
        mock_response_200.status_code = 200
        
        with patch.object(transport.client, 'build_request', return_value=mock_request), \
             patch.object(transport.client, 'send', new_callable=AsyncMock, side_effect=[mock_response_429, mock_response_200]), \
             patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
            
            result = await transport.request("GET", "/test")
            
            assert result == mock_response_200
            mock_sleep.assert_called_once_with(2.0)
        
        await transport.close()


class TestRaiseForApiError:
    """Test the raise_for_api_error static method."""

    def test_no_error_for_success_status(self):
        """Test no exception for successful status codes."""
        for status_code in [200, 201, 202, 204]:
            resp = Mock()
            resp.status_code = status_code
            
            # Should not raise any exception
            AsyncTransport.raise_for_api_error(resp)

    def test_api_error_with_json_response(self):
        """Test APIError with proper JSON error response."""
        resp = Mock()
        resp.status_code = 400
        resp.json.return_value = {
            "error": {
                "type": "validation_error",
                "message": "Invalid input",
                "code": "INVALID_INPUT"
            }
        }
        resp.headers = {"x-request-id": "req-123"}
        resp.content = b'{"error": {"type": "validation_error"}}'
        
        with pytest.raises(APIError) as exc_info:
            AsyncTransport.raise_for_api_error(resp)
        
        error = exc_info.value
        assert error.status == 400
        assert error.type == "validation_error"
        assert str(error) == "Invalid input"  # message is in the exception string
        assert error.code == "INVALID_INPUT"
        assert error.request_id == "req-123"

    def test_rate_limit_error(self):
        """Test RateLimitError for 429 status."""
        resp = Mock()
        resp.status_code = 429
        resp.json.return_value = {
            "error": {
                "type": "rate_limit_exceeded",
                "message": "Too many requests",
                "retry_after": 30.0
            }
        }
        resp.headers = {"x-request-id": "req-456"}
        resp.content = b'{"error": {"type": "rate_limit_exceeded"}}'
        
        with pytest.raises(RateLimitError) as exc_info:
            AsyncTransport.raise_for_api_error(resp)
        
        error = exc_info.value
        assert error.status == 429
        assert error.type == "rate_limit_exceeded"
        assert str(error) == "Too many requests"
        assert error.retry_after_s == 30.0

    def test_api_error_with_invalid_json(self):
        """Test APIError when response JSON is invalid."""
        resp = Mock()
        resp.status_code = 500
        resp.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        resp.text = "Internal Server Error"
        resp.headers = {"x-request-id": "req-789"}
        resp.content = b"Internal Server Error"
        
        with pytest.raises(APIError) as exc_info:
            AsyncTransport.raise_for_api_error(resp)
        
        error = exc_info.value
        assert error.status == 500
        assert error.type == "api_error"
        assert str(error) == "Internal Server Error"
        assert error.request_id == "req-789"

    def test_api_error_with_missing_error_field(self):
        """Test APIError when error field is missing from JSON."""
        resp = Mock()
        resp.status_code = 404
        resp.json.return_value = {"message": "Not found"}  # No "error" field
        resp.text = "Not Found"
        resp.headers = {}
        resp.content = b'{"message": "Not found"}'
        
        with pytest.raises(APIError) as exc_info:
            AsyncTransport.raise_for_api_error(resp)
        
        error = exc_info.value
        assert error.status == 404
        assert error.type == "api_error"
        assert str(error) == "Not Found"  # Falls back to resp.text

    def test_api_error_defaults(self):
        """Test APIError with minimal error information."""
        resp = Mock()
        resp.status_code = 422
        resp.json.return_value = {"error": {}}  # Empty error object
        resp.text = "Unprocessable Entity"
        resp.headers = {}
        resp.content = b'{"error": {}}'
        
        with pytest.raises(APIError) as exc_info:
            AsyncTransport.raise_for_api_error(resp)
        
        error = exc_info.value
        assert error.status == 422
        assert error.type == "api_error"  # Default type
        assert str(error) == "Unprocessable Entity"  # Falls back to resp.text
        assert error.code is None
        assert error.request_id is None
        assert error.retry_after_s is None


@pytest.fixture
async def transport():
    """Fixture providing a configured AsyncTransport instance."""
    config = SDKConfig(
        base_url="https://api.example.com",
        connect_timeout_s=5.0,
        read_timeout_s=30.0,
        total_timeout_s=40.0
    )
    transport = AsyncTransport(config)
    yield transport
    await transport.close()


class TestAsyncTransportIntegration:
    """Integration tests for AsyncTransport."""

    @pytest.mark.asyncio
    async def test_complete_request_flow(self, transport):
        """Test complete request flow with mocked httpx client."""
        # Mock a complete successful request
        mock_request = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        
        with patch.object(transport.client, 'build_request', return_value=mock_request), \
             patch.object(transport.client, 'send', new_callable=AsyncMock, return_value=mock_response):
            
            result = await transport.request(
                "POST", 
                "/api/test", 
                json={"test": "data"}, 
                headers={"custom": "header"}
            )
            
            assert result == mock_response
            
            # Verify build_request was called with correct parameters
            transport.client.build_request.assert_called_once_with(
                "POST", 
                "/api/test", 
                json={"test": "data"}, 
                headers={"custom": "header"}
            )

    @pytest.mark.asyncio
    async def test_request_with_keyword_arguments(self, transport):
        """Test that keyword arguments are properly passed through."""
        mock_request = Mock()
        mock_response = Mock()
        mock_response.status_code = 201
        
        with patch.object(transport.client, 'build_request', return_value=mock_request), \
             patch.object(transport.client, 'send', new_callable=AsyncMock, return_value=mock_response):
            
            result = await transport.request(
                "PUT",
                "/api/update/123",
                json={"name": "updated"},
                headers={"authorization": "Bearer token"},
                params={"version": "v1"},
                timeout=60.0
            )
            
            assert result == mock_response
            
            # Verify all kwargs were passed to build_request
            call_args = transport.client.build_request.call_args
            assert call_args[0] == ("PUT", "/api/update/123")
            assert call_args[1]["json"] == {"name": "updated"}
            assert call_args[1]["headers"]["authorization"] == "Bearer token"
            assert call_args[1]["params"] == {"version": "v1"}
            assert call_args[1]["timeout"] == 60.0
