from pydantic import BaseModel, EmailStr, Field, validator


class EmailUpdateSerializer(BaseModel):
    """Serializer for updating email."""
    email: EmailStr = Field(..., description="New email of the user")

    @validator("email")
    def validate_email(cls, value):
        if not value.endswith("@example.com"):
            raise ValueError("Email must belong to the @example.com domain")
        return value


class CheckOTPEmailSerializer(BaseModel):
    """Serializer for verifying OTP code."""
    new_email: EmailStr = Field(..., description="New email to confirm")
    code: int = Field(..., ge=10000, le=999999, description="OTP code (5-6 digits)")

    @validator("new_email")
    def validate_email_domain(cls, value):
        if "spam" in value:
            raise ValueError("Email must not contain the word 'spam'")
        return value
