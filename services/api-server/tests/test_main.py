"""
API Server - Tests
==================

STRICT TDD MODE: Tests first, then implementation.

Run tests:
    pytest                       # Run all tests
    pytest -m unit               # Run only unit tests
    pytest -m integration        # Run only integration tests
    pytest --cov=.               # Run with coverage
"""

import pytest


@pytest.mark.unit
def test_example_unit():
    """Example unit test - fast, no external dependencies."""
    assert True


@pytest.mark.integration
def test_example_integration():
    """Example integration test - may touch external services."""
    assert True
