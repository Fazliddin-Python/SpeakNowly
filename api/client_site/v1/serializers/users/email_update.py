from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional


class EmailUpdateSerializer(BaseModel):
    """Serializer for updating email."""
    email: EmailStr = Field(..., description="New email of the user")

    @validator("email")
    def validate_email(cls, value):
        if not value.endswith("@example.com"):  # Example domain validation
            raise ValueError("Email must belong to the @example.com domain")
        return value


class CheckOTPEmailSerializer(BaseModel):
    """Serializer for verifying OTP code."""
    email: EmailStr = Field(..., description="User's email")
    code: int = Field(..., ge=10000, le=99999, description="OTP code (5 digits)")

    @validator("email")
    def validate_email_domain(cls, value):
        if "spam" in value:  # Example validation for restricted words
            raise ValueError("Email must not contain the word 'spam'")
        return value