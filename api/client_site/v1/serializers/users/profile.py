from pydantic import EmailStr, Field, validator
from typing import Optional
from ..base import SafeSerializer


class ProfileSerializer(SafeSerializer):
    """Serializer for user profile operations."""
    email: Optional[EmailStr] = Field(None, description="User's email address (read-only)")
    first_name: Optional[str] = Field(None, description="User's first name")
    last_name: Optional[str] = Field(None, description="User's last name")
    age: Optional[int] = Field(None, ge=0, le=120, description="User's age (0 to 120)")
    photo: Optional[str] = Field(None, description="URL of the user's photo")
    old_password: Optional[str] = Field(None, description="Current password (required for password change)")
    new_password: Optional[str] = Field(None, min_length=8, description="New password (minimum 8 characters)")

    @validator("photo")
    def validate_photo_url(cls, value):
        if value and not value.startswith("http"):
            raise ValueError("Photo URL must start with http or https")
        return value

    @validator("new_password", always=True)
    def validate_password_change(cls, value, values):
        if value:
            if not values.get("old_password"):
                raise ValueError("Old password is required to set a new password")
            if not any(char.isdigit() for char in value):
                raise ValueError("New password must contain at least one digit")
            if not any(char.isalpha() for char in value):
                raise ValueError("New password must contain at least one letter")
        return value