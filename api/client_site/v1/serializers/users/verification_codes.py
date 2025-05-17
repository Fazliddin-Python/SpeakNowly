from pydantic import BaseModel, EmailStr, Field
from typing import Literal

class CheckOTPSerializer(BaseModel):
    """Serializer for checking verification OTP."""
    email: EmailStr = Field(..., description="Email associated with the OTP")
    code: str = Field(..., min_length=5, max_length=6, description="One-time verification code")
    verification_type: Literal[
        "register",
        "login",
        "reset_password",
        "forget_password",
        "update_email"
    ] = Field(..., description="Type of verification")

class CheckOTPResponseSerializer(BaseModel):
    """Serializer for OTP check response."""
    message: str = Field(..., description="Result message of the operation")
    access_token: str = Field(..., description="JWT access token")
