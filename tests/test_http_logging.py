"""Tests for HTTP logging utilities."""

import logging
import time
from unittest.mock import patch

import httpx
import pytest
from pytest import LogCaptureFixture

from gavaconnect.http.logging import log_request, log_response


class TestLogRequest:
    """Test log_request function."""

    @pytest.mark.asyncio
    async def test_log_request_basic(self, caplog: LogCaptureFixture):
        """Test basic request logging."""
        # Create a mock request
        req = httpx.Request("GET", "https://api.example.com/test")
        req.extensions = {}

        with caplog.at_level(logging.DEBUG, logger="gavaconnect"):
            await log_request(req)

        # Check that start_time was set
        assert "start_time" in req.extensions
        assert isinstance(req.extensions["start_time"], float)

        # Check the logged message
        assert len(caplog.records) == 1
        record = caplog.records[0]
        assert record.levelname == "DEBUG"
        assert "HTTP GET https://api.example.com/test" in record.message
        assert "headers=" in record.message

    @pytest.mark.asyncio
    async def test_log_request_with_authorization_header(self, caplog: LogCaptureFixture):
        """Test that authorization headers are removed from logs."""
        headers = {
            "authorization": "Bearer secret-token",
            "content-type": "application/json",
            "x-custom": "value",
        }
        req = httpx.Request("POST", "https://api.example.com/test", headers=headers)
        req.extensions = {}

        with caplog.at_level(logging.DEBUG, logger="gavaconnect"):
            await log_request(req)

        # Check that authorization header is not in the log
        record = caplog.records[0]
        assert "secret-token" not in record.message
        assert "Bearer" not in record.message
        # But other headers should be present
        assert "content-type" in record.message
        assert "x-custom" in record.message

    @pytest.mark.asyncio
    async def test_log_request_timing(self):
        """Test that timing is properly recorded."""
        req = httpx.Request("GET", "https://api.example.com/test")
        req.extensions = {}

        before_time = time.perf_counter()
        await log_request(req)
        after_time = time.perf_counter()

        # Check that start_time is within reasonable bounds
        start_time = req.extensions["start_time"]
        assert before_time <= start_time <= after_time


class TestLogResponse:
    """Test log_response function."""

    @pytest.mark.asyncio
    async def test_log_response_basic(self, caplog: LogCaptureFixture):
        """Test basic response logging."""
        # Create a mock request with start_time
        req = httpx.Request("GET", "https://api.example.com/test")
        req.extensions = {"start_time": time.perf_counter() - 0.1}  # 100ms ago

        # Create a mock response
        resp = httpx.Response(
            status_code=200,
            headers={"x-request-id": "req-123"},
            content=b'{"result": "success"}',
        )

        with caplog.at_level(logging.INFO, logger="gavaconnect"):
            await log_response(req, resp)

        # Check the logged message
        assert len(caplog.records) == 1
        record = caplog.records[0]
        assert record.levelname == "INFO"
        assert "HTTP GET https://api.example.com/test -> 200" in record.message
        assert "request_id=req-123" in record.message
        assert "in " in record.message and "s" in record.message  # timing info

    @pytest.mark.asyncio
    async def test_log_response_without_start_time(self, caplog: LogCaptureFixture):
        """Test response logging when start_time is missing."""
        # Create a mock request without start_time
        req = httpx.Request("POST", "https://api.example.com/test")
        req.extensions = {}

        # Create a mock response
        resp = httpx.Response(status_code=201)

        with caplog.at_level(logging.INFO, logger="gavaconnect"):
            await log_response(req, resp)

        # Should still log without error
        assert len(caplog.records) == 1
        record = caplog.records[0]
        assert "HTTP POST https://api.example.com/test -> 201" in record.message

    @pytest.mark.asyncio
    async def test_log_response_without_request_id(self, caplog: LogCaptureFixture):
        """Test response logging when request ID is missing."""
        # Create a mock request with start_time
        req = httpx.Request("GET", "https://api.example.com/test")
        req.extensions = {"start_time": time.perf_counter()}

        # Create a mock response without request ID
        resp = httpx.Response(status_code=404)

        with caplog.at_level(logging.INFO, logger="gavaconnect"):
            await log_response(req, resp)

        # Check the logged message
        record = caplog.records[0]
        assert "request_id=None" in record.message

    @pytest.mark.asyncio
    async def test_log_response_timing_calculation(self):
        """Test that timing calculation works correctly."""
        # Create a mock request with a specific start_time
        start_time = time.perf_counter() - 0.5  # 500ms ago
        req = httpx.Request("GET", "https://api.example.com/test")
        req.extensions = {"start_time": start_time}

        # Create a mock response
        resp = httpx.Response(status_code=200)

        with patch("gavaconnect.http.logging.logger") as mock_logger:
            await log_response(req, resp)

            # Check that the timing was calculated
            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args[0][0]

            # The duration should be approximately 0.5 seconds
            # Extract the duration from the log message
            import re

            match = re.search(r"in (\d+\.\d+)s", call_args)
            assert match is not None
            duration = float(match.group(1))
            assert 0.4 <= duration <= 0.6  # Allow some tolerance
