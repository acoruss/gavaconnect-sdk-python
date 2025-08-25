"""Basic credential types for authentication."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class BasicPair:
    """Basic auth credential pair for token endpoints."""

    client_id: str
    client_secret: str
