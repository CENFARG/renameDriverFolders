"""
Tests for TokenData model (Task 1.1.1)

Following Strict TDD: RED → GREEN → REFACTOR
"""
import pytest
from datetime import datetime, timedelta
from pydantic import ValidationError


@pytest.mark.unit
class TestTokenData:
    """Test TokenData Pydantic model"""

    def test_token_data_valid_creation(self):
        """Should create valid TokenData with all required fields"""
        # Arrange
        from core_renombrador.models.token import TokenData

        token_data = TokenData(
            access_token="ya29.a0AfH6...",
            refresh_token="refresh_token_123",
            token_type="Bearer",
            expires_at=datetime.now() + timedelta(hours=1),
            scope=["https://www.googleapis.com/auth/userinfo.email",
                   "https://www.googleapis.com/auth/drive.readonly"],
            user_id="user_123",
            email="user@example.com",
            issued_at=datetime.now()
        )

        # Assert
        assert token_data.access_token == "ya29.a0AfH6..."
        assert token_data.refresh_token == "refresh_token_123"
        assert token_data.token_type == "Bearer"
        assert token_data.user_id == "user_123"
        assert token_data.email == "user@example.com"
        assert len(token_data.scope) == 2

    def test_token_data_missing_required_fields(self):
        """Should raise ValidationError when required fields are missing"""
        from core_renombrador.models.token import TokenData

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            TokenData(
                access_token="ya29.a0AfH6..."
                # Missing: refresh_token, expires_at, scope, user_id, email, issued_at
            )

        errors = exc_info.value.errors()
        error_fields = {error["loc"][0] for error in errors}
        assert "refresh_token" in error_fields
        assert "expires_at" in error_fields
        assert "scope" in error_fields
        assert "user_id" in error_fields
        assert "email" in error_fields
        assert "issued_at" in error_fields

    def test_token_data_expires_in_future(self):
        """Should validate that expires_at is in the future"""
        from core_renombrador.models.token import TokenData

        # Arrange: expires_at in the past
        past_expiry = datetime.now() - timedelta(hours=1)

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            TokenData(
                access_token="token",
                refresh_token="refresh",
                expires_at=past_expiry,
                scope=["email"],
                user_id="user_123",
                email="user@example.com",
                issued_at=datetime.now()
            )

        # Should have validation error for expires_at
        errors = exc_info.value.errors()
        assert any("expires_at" in str(error.get("loc", "")) for error in errors)

    def test_token_data_serialization(self):
        """Should serialize to JSON and deserialize back correctly"""
        from core_renombrador.models.token import TokenData

        # Arrange
        original_token = TokenData(
            access_token="ya29.a0AfH6...",
            refresh_token="refresh_token_123",
            token_type="Bearer",
            expires_at=datetime.now() + timedelta(hours=1),
            scope=["email", "drive.readonly"],
            user_id="user_123",
            email="user@example.com",
            issued_at=datetime.now()
        )

        # Act: Serialize to JSON
        json_str = original_token.model_dump_json()

        # Assert: Deserialize back
        restored_token = TokenData.model_validate_json(json_str)

        assert restored_token.access_token == original_token.access_token
        assert restored_token.refresh_token == original_token.refresh_token
        assert restored_token.user_id == original_token.user_id
        assert restored_token.email == original_token.email
