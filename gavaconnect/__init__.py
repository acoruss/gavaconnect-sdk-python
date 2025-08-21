"""GavaConnect SDK for Python."""
from .checkers import KRAPINChecker


def main() -> None:
    """Main entry point for the CLI."""
    print("Hello from gavaconnect-sdk-python!")


__all__ = ["main", "KRAPINChecker"]
