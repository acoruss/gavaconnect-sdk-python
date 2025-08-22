"""GavaConnect SDK for Python."""

from ._version import __version__
from .checkers import KRAPINChecker
from .config import SDKConfig
from .errors import APIError, RateLimitError, SDKError, TransportError

# Note: AsyncGavaConnect and CheckersClient require httpx and pydantic
# Import them explicitly: from gavaconnect.facade_async import AsyncGavaConnect
# or from gavaconnect.resources.checkers import CheckersClient

__all__ = [
    "__version__",
    "SDKConfig",
    "SDKError",
    "APIError",
    "RateLimitError",
    "TransportError",
    "KRAPINChecker",
]
