#!/usr/bin/env python3
"""Smoke test for the PIN validation checker."""

import asyncio

from gavaconnect import AsyncGavaConnect, SDKConfig


async def smoke_test() -> None:
    """Run basic smoke test for the PIN checker implementation."""
    config = SDKConfig(base_url="https://sbx.kra.go.ke")
    
    async with AsyncGavaConnect(
        config,
        checkers_client_id="test_client",
        checkers_client_secret="test_secret"
    ) as sdk:
        print("✓ SDK initialized successfully")
        print("✓ Checkers client created")
        print("✓ Context manager works")
        
        # Check that the client has the expected methods
        assert hasattr(sdk.checkers, 'validate_pin')
        assert hasattr(sdk.checkers, 'validate_pin_get')
        assert hasattr(sdk.checkers, 'validate_pin_raw')
        print("✓ All required methods available")
        
        # Test PinCheckResult model
        from gavaconnect.resources.checkers import PinCheckResult
        
        # Test model with alias support
        result = PinCheckResult(PIN="A000000000B", TaxPayerName="ACME LTD", status="VALID", valid=True)
        dumped = result.model_dump(by_alias=True)
        assert dumped["PIN"] == "A000000000B"
        assert dumped["TaxPayerName"] == "ACME LTD"
        print("✓ PinCheckResult model works with aliases")
        
        print("🎉 Smoke test passed!")


if __name__ == "__main__":
    asyncio.run(smoke_test())
