import re
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional


class ProfileSerializer(BaseModel):
    """Serializer for user profile data."""
    email: EmailStr
    first_name: Optional[str] = Field(None, description="User's first name")
    last_name: Optional[str] = Field(None, description="User's last name")
    age: Optional[int] = Field(None, ge=0, le=120, description="User's age")
    photo: Optional[str] = Field(None, description="URL of the user's photo")
    tokens: int = Field(..., description="User's token balance")
    is_premium: bool = Field(..., description="Whether the user has a premium tariff")

    @validator("photo")
    def validate_photo(cls, v):
        if v is None:
            return v
        if v.startswith("http://") or v.startswith("https://") or v.startswith("/media/"):
            return v
        raise ValueError("Photo URL must start with http, https, or /media/")

    class Config:
        from_attributes = True


class ProfileUpdateSerializer(BaseModel):
    """Serializer for updating user profile fields."""
    first_name: Optional[str] = Field(None, description="User's first name")
    last_name: Optional[str] = Field(None, description="User's last name")
    age: Optional[int] = Field(None, ge=0, le=120, description="User's age")
    photo: Optional[str] = Field(None, description="URL of the user's photo")

    @validator("photo")
    def validate_photo_url(cls, value: Optional[str]) -> Optional[str]:
        if value and not (
            value.startswith("http://") or value.startswith("https://") or value.startswith("/media/")
        ):
            raise ValueError("Photo URL must start with http, https, or /media/")
        return value


class ProfilePasswordUpdateSerializer(BaseModel):
    """Serializer for updating user password."""
    old_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password (min 8 chars)")

    @validator("new_password")
    def validate_new_password(cls, value: str) -> str:
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
