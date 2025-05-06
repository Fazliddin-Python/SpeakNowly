from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, Literal


class VerificationCodeSerializer(BaseModel):
    """Serializer for verification codes."""
    id: int = Field(..., description="Unique identifier of the code")
    email: Optional[EmailStr] = Field(None, description="Email associated with the code")
    user_id: Optional[int] = Field(None, description="User ID associated with the code")
    verification_type: Literal["register", "login", "reset_password", "forget_password", "update_email"] = Field(
        ..., description="Type of verification (e.g., register, login, reset_password)"
    )
    code: int = Field(..., ge=100000, le=999999, description="Verification code (6 digits)")
    is_used: bool = Field(..., description="Whether the code has been used")
    is_expired: bool = Field(..., description="Whether the code has expired")

    @validator("code")
    def validate_code_length(cls, value):
        """Ensure the code is exactly 6 digits."""
        if len(str(value)) != 6:
            raise ValueError("Code must be exactly 6 digits")
        return value

    class Config:
        from_attributes = True