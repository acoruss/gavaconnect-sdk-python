"""Tests for telemetry graceful degradation without OpenTelemetry."""

from unittest.mock import Mock, patch

import httpx
import pytest

from gavaconnect.http.telemetry import (
    OTEL_AVAILABLE,
    otel_request_span,
    otel_response_span,
)


class TestTelemetryGracefulDegradation:
    """Test telemetry functions work without OpenTelemetry installed."""

    @pytest.mark.asyncio
    async def test_otel_request_span_without_opentelemetry(self):
        """Test that otel_request_span doesn't fail when OpenTelemetry is unavailable."""
        # Create a mock request
        request = Mock(spec=httpx.Request)
        request.method = "GET"
        request.url = "https://api.example.com/test"
        request.extensions = {}

        # Should not raise any exception
        await otel_request_span(request)

        # If OpenTelemetry is available, span should be set
        if OTEL_AVAILABLE:
            assert "otel_span" in request.extensions
        else:
            # If not available, no span should be set
            assert "otel_span" not in request.extensions

    @pytest.mark.asyncio
    async def test_otel_response_span_without_opentelemetry(self):
        """Test that otel_response_span doesn't fail when OpenTelemetry is unavailable."""
        # Create mock request and response
        request = Mock(spec=httpx.Request)
        request.extensions = {}

        response = Mock(spec=httpx.Response)
        response.status_code = 200
        response.headers = {"x-request-id": "test-123"}

        # Should not raise any exception
        await otel_response_span(request, response)

        # Extensions should be empty since no span was created
        assert "otel_span" not in request.extensions

    @pytest.mark.asyncio
    async def test_otel_response_span_with_existing_span(self):
        """Test otel_response_span with existing span in extensions."""
        if not OTEL_AVAILABLE:
            pytest.skip("OpenTelemetry not available")

        # Create mock request with span
        request = Mock(spec=httpx.Request)
        mock_span = Mock()
        request.extensions = {"otel_span": mock_span}

        response = Mock(spec=httpx.Response)
        response.status_code = 200
        response.headers = {"x-request-id": "test-123"}

        await otel_response_span(request, response)

        # Verify span methods were called
        mock_span.set_attribute.assert_called()
        mock_span.end.assert_called_once()

        # Span should be removed from extensions
        assert "otel_span" not in request.extensions

    @pytest.mark.asyncio
    async def test_otel_request_span_early_return_otel_unavailable(self):
        """Test otel_request_span returns early when OTEL_AVAILABLE is False."""
        # Temporarily patch OTEL_AVAILABLE to False
        with patch("gavaconnect.http.telemetry.OTEL_AVAILABLE", False):
            # Create a real request object
            request = httpx.Request("GET", "https://api.example.com/test")
            request.extensions = {}

            # Should return early and not add span
            await otel_request_span(request)

            # No span should be added
            assert "otel_span" not in request.extensions

    @pytest.mark.asyncio
    async def test_otel_request_span_early_return_tracer_none(self):
        """Test otel_request_span returns early when tracer is None."""
        # Temporarily patch tracer to None while keeping OTEL_AVAILABLE True
        with patch("gavaconnect.http.telemetry.OTEL_AVAILABLE", True):
            with patch("gavaconnect.http.telemetry.tracer", None):
                # Create a real request object
                request = httpx.Request("GET", "https://api.example.com/test")
                request.extensions = {}

                # Should return early and not add span
                await otel_request_span(request)

                # No span should be added
                assert "otel_span" not in request.extensions

    @pytest.mark.asyncio
    async def test_otel_response_span_early_return_otel_unavailable(self):
        """Test otel_response_span returns early when OTEL_AVAILABLE is False."""
        # Temporarily patch OTEL_AVAILABLE to False
        with patch("gavaconnect.http.telemetry.OTEL_AVAILABLE", False):
            # Create real request and response objects
            request = httpx.Request("GET", "https://api.example.com/test")
            request.extensions = {"some_other_extension": "value"}
            response = httpx.Response(status_code=200)

            # Should return early and not modify extensions
            await otel_response_span(request, response)

            # Extensions should remain unchanged
            assert request.extensions == {"some_other_extension": "value"}
