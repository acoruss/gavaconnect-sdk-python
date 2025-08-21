"""Tests for HTTP module imports and initialization."""

import pytest


class TestHttpModuleImports:
    """Test that the HTTP module imports work correctly."""

    def test_import_logging_functions(self):
        """Test importing logging functions."""
        from gavaconnect.http import log_request, log_response
        
        assert callable(log_request)
        assert callable(log_response)

    def test_import_telemetry_functions(self):
        """Test importing telemetry functions."""
        from gavaconnect.http import otel_request_span, otel_response_span
        
        assert callable(otel_request_span)
        assert callable(otel_response_span)

    def test_import_transport_class(self):
        """Test importing transport class."""
        from gavaconnect.http import AsyncTransport
        
        assert AsyncTransport is not None
        # Verify it's a class
        assert isinstance(AsyncTransport, type)

    def test_all_exports(self):
        """Test that __all__ contains expected exports."""
        import gavaconnect.http as http_module
        
        expected_exports = [
            "log_request",
            "log_response", 
            "otel_request_span",
            "otel_response_span",
            "AsyncTransport"
        ]
        
        assert hasattr(http_module, "__all__")
        
        # Check that all expected items are in __all__
        for export in expected_exports:
            assert export in http_module.__all__
            
        # Check that all items in __all__ are actually available
        for export in http_module.__all__:
            assert hasattr(http_module, export)

    def test_direct_module_import(self):
        """Test importing the module directly."""
        import gavaconnect.http
        
        # Should have a docstring
        assert gavaconnect.http.__doc__ is not None
        assert "HTTP transport layer" in gavaconnect.http.__doc__

    def test_individual_submodule_imports(self):
        """Test that individual submodules can be imported."""
        # Test individual imports don't raise errors
        import gavaconnect.http.logging
        import gavaconnect.http.telemetry
        import gavaconnect.http.transport
        
        # Verify they have the expected content
        assert hasattr(gavaconnect.http.logging, "log_request")
        assert hasattr(gavaconnect.http.telemetry, "otel_request_span")
        assert hasattr(gavaconnect.http.transport, "AsyncTransport")
