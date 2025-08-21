"""Tests for GavaConnect SDK error classes."""

import pytest

from gavaconnect import errors


class TestSDKError:
    """Tests for the base SDKError exception."""

    def test_sdk_error_inheritance(self) -> None:
        """Test that SDKError inherits from Exception."""
        assert issubclass(errors.SDKError, Exception)

    def test_sdk_error_creation(self) -> None:
        """Test that SDKError can be created with a message."""
        message = "Test error message"
        error = errors.SDKError(message)
        assert str(error) == message

    def test_sdk_error_creation_without_message(self) -> None:
        """Test that SDKError can be created without a message."""
        error = errors.SDKError()
        assert str(error) == ""

    def test_sdk_error_can_be_raised(self) -> None:
        """Test that SDKError can be raised and caught."""
        with pytest.raises(errors.SDKError) as exc_info:
            raise errors.SDKError("Test error")
        assert str(exc_info.value) == "Test error"


class TestTransportError:
    """Tests for the TransportError exception."""

    def test_transport_error_inheritance(self) -> None:
        """Test that TransportError inherits from SDKError."""
        assert issubclass(errors.TransportError, errors.SDKError)
        assert issubclass(errors.TransportError, Exception)

    def test_transport_error_creation(self) -> None:
        """Test that TransportError can be created with a message."""
        message = "Network connection failed"
        error = errors.TransportError(message)
        assert str(error) == message

    def test_transport_error_can_be_raised(self) -> None:
        """Test that TransportError can be raised and caught."""
        with pytest.raises(errors.TransportError) as exc_info:
            raise errors.TransportError("Connection timeout")
        assert str(exc_info.value) == "Connection timeout"

    def test_transport_error_caught_as_sdk_error(self) -> None:
        """Test that TransportError can be caught as SDKError."""
        with pytest.raises(errors.SDKError):
            raise errors.TransportError("Network error")


class TestSerializationError:
    """Tests for the SerializationError exception."""

    def test_serialization_error_inheritance(self) -> None:
        """Test that SerializationError inherits from SDKError."""
        assert issubclass(errors.SerializationError, errors.SDKError)
        assert issubclass(errors.SerializationError, Exception)

    def test_serialization_error_creation(self) -> None:
        """Test that SerializationError can be created with a message."""
        message = "JSON decode error"
        error = errors.SerializationError(message)
        assert str(error) == message

    def test_serialization_error_can_be_raised(self) -> None:
        """Test that SerializationError can be raised and caught."""
        with pytest.raises(errors.SerializationError) as exc_info:
            raise errors.SerializationError("Invalid JSON format")
        assert str(exc_info.value) == "Invalid JSON format"

    def test_serialization_error_caught_as_sdk_error(self) -> None:
        """Test that SerializationError can be caught as SDKError."""
        with pytest.raises(errors.SDKError):
            raise errors.SerializationError("Serialization failed")


class TestAPIError:
    """Tests for the APIError exception."""

    def test_api_error_inheritance(self) -> None:
        """Test that APIError inherits from SDKError."""
        assert issubclass(errors.APIError, errors.SDKError)
        assert issubclass(errors.APIError, Exception)

    def test_api_error_creation_with_all_parameters(self) -> None:
        """Test that APIError can be created with all parameters."""
        status = 400
        type_ = "bad_request"
        message = "Invalid request parameters"
        code = "INVALID_PARAMS"
        request_id = "req_123456"
        retry_after_s = 30.5
        body = b'{"error": "bad request"}'

        error = errors.APIError(
            status=status,
            type_=type_,
            message=message,
            code=code,
            request_id=request_id,
            retry_after_s=retry_after_s,
            body=body,
        )

        assert str(error) == message
        assert error.status == status
        assert error.type == type_
        assert error.code == code
        assert error.request_id == request_id
        assert error.retry_after_s == retry_after_s
        assert error.body == body

    def test_api_error_creation_with_required_parameters_only(self) -> None:
        """Test that APIError can be created with only required parameters."""
        status = 500
        type_ = "internal_error"
        message = "Internal server error"

        error = errors.APIError(
            status=status,
            type_=type_,
            message=message,
            code=None,
            request_id=None,
            retry_after_s=None,
            body=None,
        )

        assert str(error) == message
        assert error.status == status
        assert error.type == type_
        assert error.code is None
        assert error.request_id is None
        assert error.retry_after_s is None
        assert error.body is None

    def test_api_error_can_be_raised(self) -> None:
        """Test that APIError can be raised and caught."""
        with pytest.raises(errors.APIError) as exc_info:
            raise errors.APIError(
                status=404,
                type_="not_found",
                message="Resource not found",
                code=None,
                request_id=None,
                retry_after_s=None,
                body=None,
            )

        error = exc_info.value
        assert str(error) == "Resource not found"
        assert error.status == 404
        assert error.type == "not_found"

    def test_api_error_caught_as_sdk_error(self) -> None:
        """Test that APIError can be caught as SDKError."""
        with pytest.raises(errors.SDKError):
            raise errors.APIError(
                status=403,
                type_="forbidden",
                message="Access denied",
                code=None,
                request_id=None,
                retry_after_s=None,
                body=None,
            )

    def test_api_error_with_different_status_codes(self) -> None:
        """Test APIError with various HTTP status codes."""
        test_cases = [
            (400, "bad_request", "Bad Request"),
            (401, "unauthorized", "Unauthorized"),
            (403, "forbidden", "Forbidden"),
            (404, "not_found", "Not Found"),
            (422, "unprocessable_entity", "Validation Error"),
            (500, "internal_error", "Internal Server Error"),
            (502, "bad_gateway", "Bad Gateway"),
            (503, "service_unavailable", "Service Unavailable"),
        ]

        for status, type_, message in test_cases:
            error = errors.APIError(
                status=status,
                type_=type_,
                message=message,
                code=None,
                request_id=None,
                retry_after_s=None,
                body=None,
            )
            assert error.status == status
            assert error.type == type_
            assert str(error) == message


class TestRateLimitError:
    """Tests for the RateLimitError exception."""

    def test_rate_limit_error_inheritance(self) -> None:
        """Test that RateLimitError inherits from APIError."""
        assert issubclass(errors.RateLimitError, errors.APIError)
        assert issubclass(errors.RateLimitError, errors.SDKError)
        assert issubclass(errors.RateLimitError, Exception)

    def test_rate_limit_error_creation(self) -> None:
        """Test that RateLimitError can be created with typical rate limit parameters."""
        status = 429
        type_ = "rate_limit_exceeded"
        message = "Rate limit exceeded"
        code = "RATE_LIMIT"
        request_id = "req_rate_limit_123"
        retry_after_s = 60.0
        body = b'{"error": "rate limit exceeded", "retry_after": 60}'

        error = errors.RateLimitError(
            status=status,
            type_=type_,
            message=message,
            code=code,
            request_id=request_id,
            retry_after_s=retry_after_s,
            body=body,
        )

        assert str(error) == message
        assert error.status == status
        assert error.type == type_
        assert error.code == code
        assert error.request_id == request_id
        assert error.retry_after_s == retry_after_s
        assert error.body == body

    def test_rate_limit_error_can_be_raised(self) -> None:
        """Test that RateLimitError can be raised and caught."""
        with pytest.raises(errors.RateLimitError) as exc_info:
            raise errors.RateLimitError(
                status=429,
                type_="rate_limit",
                message="Too many requests",
                code="TOO_MANY_REQUESTS",
                request_id="req_123",
                retry_after_s=120.0,
                body=None,
            )

        error = exc_info.value
        assert str(error) == "Too many requests"
        assert error.status == 429
        assert error.retry_after_s == 120.0

    def test_rate_limit_error_caught_as_api_error(self) -> None:
        """Test that RateLimitError can be caught as APIError."""
        with pytest.raises(errors.APIError):
            raise errors.RateLimitError(
                status=429,
                type_="rate_limit",
                message="Rate limited",
                code=None,
                request_id=None,
                retry_after_s=None,
                body=None,
            )

    def test_rate_limit_error_caught_as_sdk_error(self) -> None:
        """Test that RateLimitError can be caught as SDKError."""
        with pytest.raises(errors.SDKError):
            raise errors.RateLimitError(
                status=429,
                type_="rate_limit",
                message="Rate limited",
                code=None,
                request_id=None,
                retry_after_s=None,
                body=None,
            )


class TestErrorInteractions:
    """Tests for interactions between different error types."""

    def test_all_errors_inherit_from_sdk_error(self) -> None:
        """Test that all custom errors inherit from SDKError."""
        error_classes = [
            errors.TransportError,
            errors.SerializationError,
            errors.APIError,
            errors.RateLimitError,
        ]

        for error_class in error_classes:
            assert issubclass(error_class, errors.SDKError)

    def test_exception_hierarchy_catch_order(self) -> None:
        """Test that exceptions can be caught in the correct hierarchy order."""
        # Most specific first
        try:
            raise errors.RateLimitError(
                status=429,
                type_="rate_limit",
                message="Rate limited",
                code=None,
                request_id=None,
                retry_after_s=None,
                body=None,
            )
        except errors.RateLimitError:
            caught_type = "RateLimitError"
        except errors.APIError:
            caught_type = "APIError"
        except errors.SDKError:
            caught_type = "SDKError"
        except Exception:
            caught_type = "Exception"

        assert caught_type == "RateLimitError"

        # Test APIError (but not RateLimitError) is caught as APIError
        try:
            raise errors.APIError(
                status=404,
                type_="not_found",
                message="Not found",
                code=None,
                request_id=None,
                retry_after_s=None,
                body=None,
            )
        except errors.RateLimitError:
            caught_type = "RateLimitError"
        except errors.APIError:
            caught_type = "APIError"
        except errors.SDKError:
            caught_type = "SDKError"
        except Exception:
            caught_type = "Exception"

        assert caught_type == "APIError"

    def test_error_messages_preserved(self) -> None:
        """Test that error messages are properly preserved across inheritance."""
        test_cases = [
            (errors.SDKError, "SDK error message"),
            (errors.TransportError, "Transport error message"),
            (errors.SerializationError, "Serialization error message"),
        ]

        for error_class, message in test_cases:
            error = error_class(message)
            assert str(error) == message
