import re
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, validator


class RegisterSerializer(BaseModel):
    """
    Serializer for user registration.
    """
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., min_length=8, description="User's password (minimum 8 characters)")

    @validator("email")
    def normalize_email(cls, value: str) -> str:
        return value.lower().strip()

    @validator("password")
    def validate_password(cls, value: str) -> str:
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not re.search(r"[A-Z]", value):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", value):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", value):
            raise ValueError("Password must contain at least one digit")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", value):
            raise ValueError("Password must contain at least one special character")
        return value


class RegisterResponseSerializer(BaseModel):
    """
    Serializer for registration response.
    Now returns only a confirmation message (no tokens).
    """
    message: str = Field(..., description="Informational message about the registration step")
