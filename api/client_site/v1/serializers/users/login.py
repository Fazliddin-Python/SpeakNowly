from pydantic import BaseModel, EmailStr, Field


class LoginSerializer(BaseModel):
    """Serializer for user login."""
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., min_length=8, description="User's password (minimum 8 characters)")


class AuthSerializer(BaseModel):
    """Serializer for authentication response."""
    token: str = Field(..., description="Authentication token")
    auth_type: str = Field(..., description="Type of authentication (e.g., Bearer)")