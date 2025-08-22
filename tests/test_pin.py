"""Tests for KRA PIN checker functionality."""


from gavaconnect import checkers


def test_kra_pin_checker_valid() -> None:
    """Test that a valid 6-character PIN starting with letter is correctly identified."""
    checker = checkers.KRAPINChecker("A12345")
    assert checker.check_by_id_number() == "Valid KRA PIN."


def test_kra_pin_checker_invalid_length() -> None:
    """Test that an invalid PIN (not 6 characters) is correctly identified."""
    checker = checkers.KRAPINChecker("12345")
    assert "Must be exactly 6 characters" in checker.check_by_id_number()


def test_kra_pin_checker_invalid_start_with_number() -> None:
    """Test that a PIN starting with number is rejected."""
    checker = checkers.KRAPINChecker("123456")
    assert "Must start with a letter" in checker.check_by_id_number()


def test_kra_pin_checker_invalid_special_chars() -> None:
    """Test that a PIN with special characters is rejected."""
    checker = checkers.KRAPINChecker("A123@#")
    assert "Must contain only alphanumeric characters" in checker.check_by_id_number()


def test_kra_pin_checker_empty() -> None:
    """Test that empty PIN is rejected."""
    checker = checkers.KRAPINChecker("")
    assert "Empty value" in checker.check_by_id_number()


def test_kra_pin_checker_whitespace_handling() -> None:
    """Test that PIN with surrounding whitespace is handled correctly."""
    checker = checkers.KRAPINChecker("  A12345  ")
    assert checker.check_by_id_number() == "Valid KRA PIN."


def test_kra_pin_checker_none_input() -> None:
    """Test that None input is handled gracefully."""
    checker = checkers.KRAPINChecker(None)  # type: ignore[arg-type]
    result = checker.check_by_id_number()
    assert "Empty value" in result
