"""
Tests for TokenStore abstract interface (Task 1.1.2)

Following Strict TDD: RED → GREEN → REFACTOR
"""
import pytest
from abc import ABC, abstractmethod


@pytest.mark.unit
class TestTokenStore:
    """Test TokenStore abstract interface"""

    def test_token_store_is_abstract(self):
        """Should be an abstract base class"""
        from core_renombrador.token_store import TokenStore

        # Assert: TokenStore should be abstract
        assert issubclass(TokenStore, ABC)

        # Cannot instantiate abstract class
        with pytest.raises(TypeError):
            TokenStore()

    def test_token_store_has_required_methods(self):
        """Should have all required abstract methods"""
        from core_renombrador.token_store import TokenStore

        # Get abstract methods
        abstract_methods = TokenStore.__abstractmethods__

        # Assert: Required methods must be abstract
        required_methods = {
            "get_token",
            "store_token",
            "invalidate",
        }

        assert required_methods.issubset(abstract_methods), \
            f"Missing abstract methods: {required_methods - abstract_methods}"
