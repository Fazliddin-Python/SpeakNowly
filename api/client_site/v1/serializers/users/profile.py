from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional


class ProfileSerializer(BaseModel):
    """Serializer for user profile data."""
    email: EmailStr
    first_name: Optional[str] = Field(None, description="User's first name")
    last_name: Optional[str] = Field(None, description="User's last name")
    age: Optional[int] = Field(None, ge=0, le=120, description="User's age")
    photo: Optional[str] = Field(None, description="URL of the user's photo")

    @validator("photo")
    def validate_photo_url(cls, value: Optional[str]) -> Optional[str]:
        if value and not value.startswith("http"):
            raise ValueError("Photo URL must start with http or https")
        return value

    class Config:
        from_attributes = True


class ProfileUpdateSerializer(BaseModel):
    """Serializer for updating user profile fields."""
    email: Optional[EmailStr] = Field(None, description="New email address")
    first_name: Optional[str] = Field(None, description="User's first name")
    last_name: Optional[str] = Field(None, description="User's last name")
    age: Optional[int] = Field(None, ge=0, le=120, description="User's age")
    photo: Optional[str] = Field(None, description="URL of the user's photo")

    @validator("email")
    def normalize_email(cls, v: str) -> str:
        return v.lower().strip()

    @validator("photo")
    def validate_photo_url(cls, value: Optional[str]) -> Optional[str]:
        if value and not value.startswith("http"):
            raise ValueError("Photo URL must start with http or https")
        return value


class ProfilePasswordUpdateSerializer(BaseModel):
    """Serializer for updating user password."""
    old_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password (min 8 chars)")

    @validator("new_password")
    def validate_new_password(cls, value: str) -> str:
        if not any(ch.isdigit() for ch in value):
            raise ValueError("New password must include at least one digit")
        if not any(ch.isalpha() for ch in value):
            raise ValueError("New password must include at least one letter")
        return value