"""
TokenData model for OAuth token management (Task 1.1.1)

Following Strict TDD: GREEN phase - Minimal implementation to pass tests
"""
from datetime import datetime
from typing import List

from pydantic import BaseModel, field_validator


class TokenData(BaseModel):
    """
    OAuth token data structure

    Attributes:
        access_token: The OAuth access token
        refresh_token: The OAuth refresh token
        token_type: Token type (default: "Bearer")
        expires_at: UTC timestamp when token expires
        scope: List of OAuth scopes
        user_id: Unique user identifier
        email: User email address
        issued_at: When the token was issued
    """

    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_at: datetime
    scope: List[str]
    user_id: str
    email: str
    issued_at: datetime

    @field_validator("expires_at")
    @classmethod
    def expires_at_must_be_in_future(cls, v: datetime) -> datetime:
        """Validate that expires_at is in the future"""
        if v <= datetime.now():
            raise ValueError("expires_at must be in the future")
        return v
