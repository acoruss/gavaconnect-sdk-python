"""Tests for HTTP telemetry utilities."""

import httpx
import pytest
from unittest.mock import Mock, patch

from gavaconnect.http.telemetry import otel_request_span, otel_response_span


class TestOtelRequestSpan:
    """Test otel_request_span function."""

    @pytest.mark.asyncio
    async def test_otel_request_span_basic(self):
        """Test basic OpenTelemetry span creation."""
        # Create a mock request
        req = httpx.Request("GET", "https://api.example.com/test")
        req.extensions = {}
        
        # Mock the tracer
        with patch("gavaconnect.http.telemetry.tracer") as mock_tracer:
            mock_span = Mock()
            mock_tracer.start_span.return_value = mock_span
            
            await otel_request_span(req)
            
            # Verify span creation
            mock_tracer.start_span.assert_called_once_with(
                "http.client",
                attributes={
                    "http.method": "GET", 
                    "http.url": "https://api.example.com/test"
                }
            )
            
            # Verify span is stored in extensions
            assert req.extensions["otel_span"] == mock_span

    @pytest.mark.asyncio
    async def test_otel_request_span_different_methods(self):
        """Test span creation with different HTTP methods."""
        methods_and_urls = [
            ("POST", "https://api.example.com/create"),
            ("PUT", "https://api.example.com/update/123"),
            ("DELETE", "https://api.example.com/delete/456"),
            ("PATCH", "https://api.example.com/patch/789")
        ]
        
        for method, url in methods_and_urls:
            req = httpx.Request(method, url)
            req.extensions = {}
            
            with patch("gavaconnect.http.telemetry.tracer") as mock_tracer:
                mock_span = Mock()
                mock_tracer.start_span.return_value = mock_span
                
                await otel_request_span(req)
                
                # Verify correct attributes
                mock_tracer.start_span.assert_called_once_with(
                    "http.client",
                    attributes={"http.method": method, "http.url": url}
                )


class TestOtelResponseSpan:
    """Test otel_response_span function."""

    @pytest.mark.asyncio
    async def test_otel_response_span_basic(self):
        """Test basic OpenTelemetry span completion."""
        # Create a mock request with an otel span
        req = httpx.Request("GET", "https://api.example.com/test")
        mock_span = Mock()
        req.extensions = {"otel_span": mock_span}
        
        # Create a mock response
        resp = httpx.Response(
            status_code=200,
            headers={"x-request-id": "req-123"}
        )
        
        await otel_response_span(req, resp)
        
        # Verify span attributes were set
        mock_span.set_attribute.assert_any_call("http.status_code", 200)
        mock_span.set_attribute.assert_any_call("http.response.request_id", "req-123")
        
        # Verify span was ended
        mock_span.end.assert_called_once()
        
        # Verify span was removed from extensions
        assert "otel_span" not in req.extensions

    @pytest.mark.asyncio
    async def test_otel_response_span_without_request_id(self):
        """Test span completion when response has no request ID."""
        # Create a mock request with an otel span
        req = httpx.Request("POST", "https://api.example.com/test")
        mock_span = Mock()
        req.extensions = {"otel_span": mock_span}
        
        # Create a mock response without request ID
        resp = httpx.Response(status_code=404)
        
        await otel_response_span(req, resp)
        
        # Verify only status code was set (no request ID)
        mock_span.set_attribute.assert_called_once_with("http.status_code", 404)
        
        # Verify span was still ended
        mock_span.end.assert_called_once()

    @pytest.mark.asyncio
    async def test_otel_response_span_no_span_in_request(self):
        """Test span completion when no span exists in request."""
        # Create a mock request without an otel span
        req = httpx.Request("GET", "https://api.example.com/test")
        req.extensions = {}
        
        # Create a mock response
        resp = httpx.Response(status_code=200)
        
        # Should not raise an error
        await otel_response_span(req, resp)
        
        # Extensions should still be empty
        assert req.extensions == {}

    @pytest.mark.asyncio
    async def test_otel_response_span_different_status_codes(self):
        """Test span completion with different status codes."""
        status_codes = [200, 201, 400, 401, 404, 500, 502]
        
        for status_code in status_codes:
            req = httpx.Request("GET", "https://api.example.com/test")
            mock_span = Mock()
            req.extensions = {"otel_span": mock_span}
            
            resp = httpx.Response(status_code=status_code)
            
            await otel_response_span(req, resp)
            
            # Verify correct status code was set
            mock_span.set_attribute.assert_called_with("http.status_code", status_code)
            mock_span.end.assert_called_once()
            
            # Reset for next iteration
            mock_span.reset_mock()

    @pytest.mark.asyncio
    async def test_otel_response_span_with_existing_extensions(self):
        """Test that other extensions are preserved."""
        # Create a mock request with multiple extensions
        req = httpx.Request("GET", "https://api.example.com/test")
        mock_span = Mock()
        req.extensions = {
            "otel_span": mock_span,
            "start_time": 12345.0,
            "custom_data": "test_value"
        }
        
        # Create a mock response
        resp = httpx.Response(status_code=200)
        
        await otel_response_span(req, resp)
        
        # Verify span was removed but other extensions remain
        assert "otel_span" not in req.extensions
        assert req.extensions["start_time"] == 12345.0
        assert req.extensions["custom_data"] == "test_value"

    @pytest.mark.asyncio
    async def test_integration_request_and_response_spans(self):
        """Test integration between request and response span functions."""
        # Create a mock request
        req = httpx.Request("POST", "https://api.example.com/test")
        req.extensions = {}
        
        # Mock the tracer for request span
        with patch("gavaconnect.http.telemetry.tracer") as mock_tracer:
            mock_span = Mock()
            mock_tracer.start_span.return_value = mock_span
            
            # Start request span
            await otel_request_span(req)
            
            # Verify span is in extensions
            assert req.extensions["otel_span"] == mock_span
            
            # Create response and complete span
            resp = httpx.Response(
                status_code=201,
                headers={"x-request-id": "integration-test-123"}
            )
            
            await otel_response_span(req, resp)
            
            # Verify span completion
            mock_span.set_attribute.assert_any_call("http.status_code", 201)
            mock_span.set_attribute.assert_any_call("http.response.request_id", "integration-test-123")
            mock_span.end.assert_called_once()
            
            # Verify span was removed
            assert "otel_span" not in req.extensions
