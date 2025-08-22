#!/usr/bin/env python3
"""Test import behavior in different scenarios."""

def test_basic_imports():
    """Test that basic imports work without httpx/pydantic."""
    try:
        import gavaconnect
        print("✓ Basic gavaconnect import successful")
        
        from gavaconnect import SDKConfig, APIError
        print("✓ Basic classes import successful")
        
        # Test that we can import credentials without httpx
        from gavaconnect.auth.credentials import BasicPair
        pair = BasicPair("test", "secret")
        print(f"✓ BasicPair created: client_id={pair.client_id}")
        
    except Exception as e:
        print(f"✗ Basic import failed: {e}")
        return False
    
    return True


def test_full_imports():
    """Test that full imports work with dependencies."""
    try:
        from gavaconnect.facade_async import AsyncGavaConnect
        print("✓ AsyncGavaConnect import successful")
        
        from gavaconnect.resources.checkers import CheckersClient, PinCheckResult
        print("✓ CheckersClient and PinCheckResult import successful")
        
        # Test creating a model
        result = PinCheckResult(PIN="A000000000B", valid=True)
        print(f"✓ PinCheckResult created: pin={result.pin}")
        
    except Exception as e:
        print(f"✗ Full import failed: {e}")
        return False
    
    return True


if __name__ == "__main__":
    print("Testing gavaconnect imports...")
    basic_ok = test_basic_imports()
    print()
    full_ok = test_full_imports()
    print()
    
    if basic_ok and full_ok:
        print("🎉 All import tests passed!")
    else:
        print("❌ Some import tests failed")
        exit(1)
