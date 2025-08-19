"""Test the main module functionality."""

import pytest
from gavaconnect_sdk_python import main


def test_main_function_exists() -> None:
    """Test that main function exists and is callable."""
    assert callable(main)


def test_main_function_runs() -> None:
    """Test that main function runs without error."""
    # This should not raise an exception
    main()


def test_main_function_output(capsys: pytest.CaptureFixture[str]) -> None:
    """Test that main function produces expected output."""
    main()
    captured = capsys.readouterr()
    assert "Hello from gavaconnect-sdk-python!" in captured.out
