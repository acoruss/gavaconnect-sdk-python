"""Tests for idempotency helpers."""

import datetime
import uuid
from unittest.mock import Mock, patch

import httpx

from gavaconnect.helpers.idempotency import (
    _can_retry,
    _full_jitter,
    _is_idempotent,
    _parse_retry_after,
    idempotency_headers,
)


class TestIdempotencyHeaders:
    """Test idempotency_headers function."""

    def test_with_provided_key(self):
        """Test that provided key is used in headers."""
        test_key = "test-key-123"
        result = idempotency_headers(key=test_key)

        assert result == {"idempotency-key": test_key}
        assert isinstance(result, dict)
        assert len(result) == 1

    def test_with_none_key(self):
        """Test that UUID is generated when key is None."""
        result = idempotency_headers(key=None)

        assert "idempotency-key" in result
        assert isinstance(result["idempotency-key"], str)
        # Verify it's a valid UUID format
        uuid.UUID(result["idempotency-key"])

    def test_with_no_key_parameter(self):
        """Test that UUID is generated when no key parameter is provided."""
        result = idempotency_headers()

        assert "idempotency-key" in result
        assert isinstance(result["idempotency-key"], str)
        # Verify it's a valid UUID format
        uuid.UUID(result["idempotency-key"])

    def test_empty_string_key(self):
        """Test that empty string key generates UUID."""
        result = idempotency_headers(key="")

        assert "idempotency-key" in result
        assert isinstance(result["idempotency-key"], str)
        # Verify it's a valid UUID format (empty string is falsy)
        uuid.UUID(result["idempotency-key"])

    def test_whitespace_key(self):
        """Test that whitespace-only key is preserved."""
        test_key = "   "
        result = idempotency_headers(key=test_key)

        assert result == {"idempotency-key": test_key}

    @patch("uuid.uuid4")
    def test_uuid_generation_called(self, mock_uuid4: Mock) -> None:
        """Test that uuid.uuid4 is called when no key provided."""
        mock_uuid = uuid.UUID("12345678-1234-5678-1234-567812345678")
        mock_uuid4.return_value = mock_uuid

        result = idempotency_headers()

        mock_uuid4.assert_called_once()
        assert result["idempotency-key"] == str(mock_uuid)

    def test_different_calls_generate_different_uuids(self):
        """Test that consecutive calls without keys generate different UUIDs."""
        result1 = idempotency_headers()
        result2 = idempotency_headers()

        assert result1["idempotency-key"] != result2["idempotency-key"]

    def test_return_type_annotation(self):
        """Test that return type matches annotation."""
        result = idempotency_headers("test")
        assert isinstance(result, dict)

        for key, value in result.items():
            assert isinstance(key, str)
            assert isinstance(value, str)


class TestFullJitter:
    """Test _full_jitter function."""

    def test_full_jitter_calculation(self):
        """Test jitter calculation with different inputs."""
        # Test with base=1.0, attempt=1, cap=10.0
        result = _full_jitter(1.0, 1, 10.0)
        # Should be uniform random between 0 and min(cap, base*2^attempt) = min(10, 1*2) = 2
        assert 0.0 <= result <= 2.0

        # Test with base=0.5, attempt=2, cap=10.0
        result = _full_jitter(0.5, 2, 10.0)
        # Should be uniform random between 0 and min(10, 0.5*4) = 2.0
        assert 0.0 <= result <= 2.0

        # Test with base=0.2, attempt=3, cap=1.0
        result = _full_jitter(0.2, 3, 1.0)
        # Should be uniform random between 0 and min(1.0, 0.2*8) = 1.0
        assert 0.0 <= result <= 1.0

    def test_full_jitter_zero_base(self):
        """Test jitter with zero base."""
        result = _full_jitter(0.0, 5, 10.0)
        assert result == 0.0

    def test_full_jitter_zero_attempt(self):
        """Test jitter with zero attempt."""
        result = _full_jitter(2.0, 0, 10.0)
        # Should be uniform random between 0 and min(10, 2*1) = 2
        assert 0.0 <= result <= 2.0


class TestParseRetryAfter:
    """Test _parse_retry_after function."""

    def test_parse_retry_after_none(self):
        """Test parsing None value."""
        result = _parse_retry_after(None)
        assert result is None

    def test_parse_retry_after_empty_string(self):
        """Test parsing empty string."""
        result = _parse_retry_after("")
        assert result is None

    def test_parse_retry_after_numeric_seconds(self):
        """Test parsing numeric seconds."""
        result = _parse_retry_after("30")
        assert result == 30.0

        result = _parse_retry_after("5.5")
        assert result == 5.5

        result = _parse_retry_after("0")
        assert result == 0.0

    def test_parse_retry_after_negative_seconds(self):
        """Test parsing negative seconds."""
        result = _parse_retry_after("-5")
        assert result is None

    def test_parse_retry_after_invalid_numeric(self):
        """Test parsing invalid numeric values."""
        result = _parse_retry_after("abc")
        assert result is None

        result = _parse_retry_after("30.5.1")
        assert result is None

    def test_parse_retry_after_http_date(self):
        """Test parsing HTTP date format."""
        # Test with a future date
        with patch('gavaconnect.helpers.idempotency.datetime') as mock_datetime:
            # Mock current time
            mock_now = datetime.datetime(2023, 1, 1, 12, 0, 0, tzinfo=datetime.timezone.utc)
            mock_datetime.datetime.now.return_value = mock_now
            mock_datetime.UTC = datetime.timezone.utc
            
            # Test future date (30 seconds later)
            result = _parse_retry_after("Sun, 01 Jan 2023 12:00:30 GMT")
            assert result == 30.0

    def test_parse_retry_after_past_date(self):
        """Test parsing past HTTP date."""
        with patch('gavaconnect.helpers.idempotency.datetime') as mock_datetime:
            # Mock current time
            mock_now = datetime.datetime(2023, 1, 1, 12, 0, 30, tzinfo=datetime.timezone.utc)
            mock_datetime.datetime.now.return_value = mock_now
            mock_datetime.UTC = datetime.timezone.utc
            
            # Test past date (same time but earlier)
            result = _parse_retry_after("Sun, 01 Jan 2023 12:00:00 GMT")
            assert result == 0.0

    def test_parse_retry_after_exception_handling(self):
        """Test exception handling in HTTP date parsing."""
        with patch('gavaconnect.helpers.idempotency.parsedate_to_datetime') as mock_parse:
            # Mock an exception during parsing
            mock_parse.side_effect = Exception("Parsing error")
            
            result = _parse_retry_after("Some date string")
            assert result is None

    def test_parse_retry_after_none_datetime(self):
        """Test when parsedate_to_datetime returns None."""
        with patch('gavaconnect.helpers.idempotency.parsedate_to_datetime') as mock_parse:
            # Mock returning None
            mock_parse.return_value = None
            
            result = _parse_retry_after("Invalid date format")
            assert result is None

    def test_parse_retry_after_naive_datetime(self):
        """Test when parsedate_to_datetime returns a naive datetime (no timezone)."""
        with patch('gavaconnect.helpers.idempotency.parsedate_to_datetime') as mock_parse, \
             patch('gavaconnect.helpers.idempotency.datetime') as mock_datetime:
            
            # Mock a naive datetime (no timezone)
            naive_dt = datetime.datetime(2023, 1, 1, 12, 0, 30)
            mock_parse.return_value = naive_dt
            
            # Mock current time
            mock_now = datetime.datetime(2023, 1, 1, 12, 0, 0, tzinfo=datetime.timezone.utc)
            mock_datetime.datetime.now.return_value = mock_now
            mock_datetime.UTC = datetime.timezone.utc
            
            result = _parse_retry_after("Sun, 01 Jan 2023 12:00:30 GMT")
            assert result == 30.0

    def test_parse_retry_after_invalid_date(self):
        """Test parsing invalid HTTP date."""
        result = _parse_retry_after("Invalid Date")
        assert result is None

        result = _parse_retry_after("Not a date at all")
        assert result is None


class TestIsIdempotent:
    """Test _is_idempotent function."""

    def test_idempotent_methods(self):
        """Test that idempotent methods are correctly identified."""
        assert _is_idempotent("GET") is True
        assert _is_idempotent("HEAD") is True
        assert _is_idempotent("OPTIONS") is True
        assert _is_idempotent("DELETE") is True

    def test_non_idempotent_methods(self):
        """Test that non-idempotent methods are correctly identified."""
        assert _is_idempotent("POST") is False
        assert _is_idempotent("PUT") is False
        assert _is_idempotent("PATCH") is False

    def test_case_insensitive(self):
        """Test that method comparison is case insensitive."""
        assert _is_idempotent("get") is True
        assert _is_idempotent("Get") is True
        assert _is_idempotent("GET") is True
        assert _is_idempotent("post") is False
        assert _is_idempotent("Post") is False
        assert _is_idempotent("POST") is False

    def test_unknown_methods(self):
        """Test unknown HTTP methods."""
        assert _is_idempotent("UNKNOWN") is False
        assert _is_idempotent("") is False


class TestCanRetry:
    """Test _can_retry function."""

    def test_can_retry_idempotent_methods(self):
        """Test that idempotent methods can be retried."""
        req = httpx.Request("GET", "https://example.com")
        assert _can_retry("GET", req) is True

        req = httpx.Request("HEAD", "https://example.com")
        assert _can_retry("HEAD", req) is True

        req = httpx.Request("OPTIONS", "https://example.com")
        assert _can_retry("OPTIONS", req) is True

        req = httpx.Request("DELETE", "https://example.com")
        assert _can_retry("DELETE", req) is True

    def test_can_retry_non_idempotent_without_key(self):
        """Test that non-idempotent methods without idempotency key cannot be retried."""
        req = httpx.Request("POST", "https://example.com")
        assert _can_retry("POST", req) is False

        req = httpx.Request("PUT", "https://example.com")
        assert _can_retry("PUT", req) is False

        req = httpx.Request("PATCH", "https://example.com")
        assert _can_retry("PATCH", req) is False

    def test_can_retry_non_idempotent_with_key(self):
        """Test that non-idempotent methods with idempotency key can be retried."""
        req = httpx.Request("POST", "https://example.com", headers={"idempotency-key": "test-key"})
        assert _can_retry("POST", req) is True

        req = httpx.Request("PUT", "https://example.com", headers={"Idempotency-Key": "test-key"})
        assert _can_retry("PUT", req) is True

        req = httpx.Request("PATCH", "https://example.com", headers={"IDEMPOTENCY-KEY": "test-key"})
        assert _can_retry("PATCH", req) is True

    def test_can_retry_case_insensitive_header(self):
        """Test that idempotency key header check is case insensitive."""
        req = httpx.Request("POST", "https://example.com", headers={"idempotency-key": "test"})
        assert _can_retry("POST", req) is True

        req = httpx.Request("POST", "https://example.com", headers={"Idempotency-Key": "test"})
        assert _can_retry("POST", req) is True

        req = httpx.Request("POST", "https://example.com", headers={"IDEMPOTENCY-KEY": "test"})
        assert _can_retry("POST", req) is True
