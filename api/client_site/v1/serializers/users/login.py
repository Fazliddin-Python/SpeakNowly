from pydantic import BaseModel, EmailStr, Field
from typing import Literal, Optional


class LoginSerializer(BaseModel):
    """Serializer for user login."""
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., min_length=8, description="User's password (minimum 8 characters)")


class OAuth2SignInSerializer(BaseModel):
    """Serializer for OAuth2 sign-in request."""
    token: str = Field(..., description="OAuth2 provider token")
    auth_type: Literal['google', 'apple'] = Field(..., description="OAuth2 provider type")
    client_id: str = Field(..., description="OAuth2 client ID for Apple verification")


class AuthResponseSerializer(BaseModel):
    """Serializer for authentication response."""
    token: str
    refresh_token: Optional[str] = None
    auth_type: str