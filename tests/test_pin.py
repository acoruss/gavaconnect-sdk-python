"""Tests for KRA PIN checker functionality."""

from gavaconnect import checkers


def test_kra_pin_checker_valid() -> None:
    """Test that a valid 6-digit PIN is correctly identified."""
    checker = checkers.KRAPINChecker("123456")
    assert checker.check_by_id_number() == "Valid KRA PIN."


def test_kra_pin_checker_invalid() -> None:
    """Test that an invalid PIN (not 6 digits) is correctly identified."""
    checker = checkers.KRAPINChecker("12345")
    assert checker.check_by_id_number() == "Invalid KRA PIN."
