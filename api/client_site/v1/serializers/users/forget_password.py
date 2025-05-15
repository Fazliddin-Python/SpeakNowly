from pydantic import BaseModel, EmailStr, Field

class ForgetPasswordSerializer(BaseModel):
    """Serializer for requesting a password reset."""
    email: EmailStr = Field(..., description="Email address of the user")


class ResetPasswordSerializer(BaseModel):
    """Serializer for verifying OTP and setting a new password in one step."""
    email: EmailStr = Field(..., description="Email address of the user")
    code: int = Field(..., description="Verification code sent to the email")
    new_password: str = Field(..., min_length=8, description="New password (minimum 8 characters)")

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "code": 123456,
                "new_password": "NewPass123"
            }
        }
