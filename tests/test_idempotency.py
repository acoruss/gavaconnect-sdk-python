"""Tests for idempotency helpers."""

import uuid
from unittest.mock import Mock, patch

from gavaconnect.helpers.idempotency import idempotency_headers


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

    @patch('uuid.uuid4')
    def test_uuid_generation_called(self, mock_uuid4: Mock) -> None:
        """Test that uuid.uuid4 is called when no key provided."""
        mock_uuid = uuid.UUID('12345678-1234-5678-1234-567812345678')
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
