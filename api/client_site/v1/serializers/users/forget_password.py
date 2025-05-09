from pydantic import EmailStr, Field
from ..base import BaseSerializer


class ForgetPasswordSerializer(BaseSerializer):
    """Serializer for requesting a password reset."""
    email: EmailStr = Field(..., description="Email address of the user")


class SetNewPasswordSerializer(BaseSerializer):
    """Serializer for setting a new password."""
    password: str = Field(..., min_length=8, description="New password (minimum 8 characters)")
    verification_code: int = Field(..., description="Verification code sent to the email")