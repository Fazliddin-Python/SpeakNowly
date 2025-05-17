from pydantic import BaseModel, EmailStr, Field
from typing import Literal

class ResendOTPSchema(BaseModel):
    email: EmailStr = Field(..., description="Email to resend the verification code")
    verification_type: Literal[
        "register",
        "login",
        "reset_password",
        "forget_password",
        "update_email"
    ] = Field(..., description="Type of verification")

class ResendOTPResponseSerializer(BaseModel):
    message: str = Field(..., description="Result message of the operation")