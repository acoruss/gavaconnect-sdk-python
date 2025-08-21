"""Tests for basic authentication module."""

import base64

import httpx
import pytest

from gavaconnect.auth.basic import BasicAuthPolicy, BasicCredentials


class TestBasicCredentials:
    """Test BasicCredentials dataclass."""

    def test_creation(self):
        """Test creating BasicCredentials."""
        creds = BasicCredentials(client_id="test_id", client_secret="test_secret")
        assert creds.client_id == "test_id"
        assert creds.client_secret == "test_secret"

    def test_immutable(self):
        """Test that BasicCredentials is immutable."""
        creds = BasicCredentials(client_id="test_id", client_secret="test_secret")
        with pytest.raises(AttributeError):
            creds.client_id = "new_id"


class TestBasicAuthPolicy:
    """Test BasicAuthPolicy class."""

    def test_init(self):
        """Test BasicAuthPolicy initialization."""
        creds = BasicCredentials(client_id="test_id", client_secret="test_secret")
        policy = BasicAuthPolicy(creds)

        # Verify the header is created correctly
        expected_token = base64.b64encode(b"test_id:test_secret").decode()
        assert policy._header == f"Basic {expected_token}"

    @pytest.mark.asyncio
    async def test_authorize(self):
        """Test authorization of a request."""
        creds = BasicCredentials(client_id="test_id", client_secret="test_secret")
        policy = BasicAuthPolicy(creds)

        request = httpx.Request("GET", "https://example.com")
        await policy.authorize(request)

        expected_token = base64.b64encode(b"test_id:test_secret").decode()
        assert request.headers["authorization"] == f"Basic {expected_token}"

    @pytest.mark.asyncio
    async def test_on_unauthorized(self):
        """Test unauthorized response handling."""
        creds = BasicCredentials(client_id="test_id", client_secret="test_secret")
        policy = BasicAuthPolicy(creds)

        # Basic auth cannot refresh, so should always return False
        result = await policy.on_unauthorized()
        assert result is False

    def test_different_credentials(self):
        """Test with different credentials produce different headers."""
        creds1 = BasicCredentials(client_id="id1", client_secret="secret1")
        creds2 = BasicCredentials(client_id="id2", client_secret="secret2")

        policy1 = BasicAuthPolicy(creds1)
        policy2 = BasicAuthPolicy(creds2)

        assert policy1._header != policy2._header

    def test_special_characters_in_credentials(self):
        """Test credentials with special characters."""
        creds = BasicCredentials(client_id="test:id", client_secret="test@secret!")
        policy = BasicAuthPolicy(creds)

        expected_token = base64.b64encode(b"test:id:test@secret!").decode()
        assert policy._header == f"Basic {expected_token}"
