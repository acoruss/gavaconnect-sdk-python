"""Tests for auth module imports and exports."""

import pytest

from gavaconnect import auth
from gavaconnect.auth import (
    BasicAuthPolicy,
    BasicCredentials,
    BearerAuthPolicy,
    ClientCredentialsProvider,
    TokenProvider,
)


class TestAuthModuleImports:
    """Test that auth module exports work correctly."""

    def test_all_exports_available(self):
        """Test that all expected exports are available."""
        # Test direct imports
        assert BasicAuthPolicy is not None
        assert BasicCredentials is not None
        assert BearerAuthPolicy is not None
        assert TokenProvider is not None
        assert ClientCredentialsProvider is not None

    def test_module_has_all_attribute(self):
        """Test that __all__ is properly defined."""
        assert hasattr(auth, '__all__')
        assert isinstance(auth.__all__, list)
        
        expected_exports = {
            "BasicAuthPolicy",
            "BasicCredentials", 
            "BearerAuthPolicy",
            "TokenProvider",
            "ClientCredentialsProvider",
        }
        
        assert set(auth.__all__) == expected_exports

    def test_module_docstring(self):
        """Test that module has proper docstring."""
        assert auth.__doc__ is not None
        assert "Authentication module for GavaConnect SDK" in auth.__doc__

    def test_classes_importable_from_module(self):
        """Test that classes can be imported from the module."""
        assert hasattr(auth, 'BasicAuthPolicy')
        assert hasattr(auth, 'BasicCredentials')
        assert hasattr(auth, 'BearerAuthPolicy')
        assert hasattr(auth, 'TokenProvider')
        assert hasattr(auth, 'ClientCredentialsProvider')

    def test_class_types(self):
        """Test that imported classes are the correct types."""
        from gavaconnect.auth.basic import BasicAuthPolicy as BasicAuthPolicyOrig
        from gavaconnect.auth.basic import BasicCredentials as BasicCredentialsOrig
        from gavaconnect.auth.bearer import BearerAuthPolicy as BearerAuthPolicyOrig
        from gavaconnect.auth.bearer import TokenProvider as TokenProviderOrig
        from gavaconnect.auth.providers import ClientCredentialsProvider as ClientCredentialsProviderOrig
        
        assert BasicAuthPolicy is BasicAuthPolicyOrig
        assert BasicCredentials is BasicCredentialsOrig
        assert BearerAuthPolicy is BearerAuthPolicyOrig
        assert TokenProvider is TokenProviderOrig
        assert ClientCredentialsProvider is ClientCredentialsProviderOrig
