from pydantic import EmailStr, Field, validator
from typing import Optional
from datetime import datetime
from ..base import SafeSerializer, BaseSerializer


class UserBaseSerializer(BaseSerializer):
    """Base serializer for user-related operations."""
    email: EmailStr = Field(..., description="User's email address")
    first_name: Optional[str] = Field(None, description="User's first name")
    last_name: Optional[str] = Field(None, description="User's last name")
    age: Optional[int] = Field(None, ge=0, le=120, description="User's age (0 to 120)")
    photo: Optional[str] = Field(None, description="URL of the user's photo")
    is_active: bool = Field(..., description="Whether the user is active")
    is_verified: bool = Field(..., description="Whether the user is verified")
    tokens: int = Field(..., description="Number of tokens the user has")

    @validator("photo")
    def validate_photo_url(cls, value):
        if value and not value.startswith("http"):
            raise ValueError("Photo URL must start with http or https")
        return value


class UserCreateSerializer(UserBaseSerializer):
    """Serializer for creating a user."""
    password: str = Field(..., min_length=8, description="User's password (minimum 8 characters)")

    @validator("password")
    def validate_password(cls, value):
        if not any(char.isdigit() for char in value):
            raise ValueError("Password must contain at least one digit")
        if not any(char.isalpha() for char in value):
            raise ValueError("Password must contain at least one letter")
        return value


class UserUpdateSerializer(UserBaseSerializer):
    """Serializer for updating a user."""
    email: Optional[EmailStr] = Field(None, description="Updated user's email")
    is_active: Optional[bool] = Field(None, description="User's active status")
    is_staff: Optional[bool] = Field(None, description="Whether the user is a staff member")
    is_superuser: Optional[bool] = Field(None, description="Whether the user is a superuser")


class UserResponseSerializer(UserBaseSerializer):
    """Serializer for user response data."""
    id: int = Field(..., description="Unique identifier of the user")
    is_verified: bool = Field(..., description="Whether the user is verified")
    tokens: int = Field(..., ge=0, description="Number of tokens the user has")
    is_active: bool = Field(..., description="Whether the user is active")
    is_staff: bool = Field(..., description="Whether the user is a staff member")
    is_superuser: bool = Field(..., description="Whether the user is a superuser")
    last_login: Optional[datetime] = Field(None, description="User's last login time")

    class Config:
        from_attributes = True 


class UserActivityLogSerializer(SafeSerializer):
    """Serializer for user activity logs."""
    user_id: int = Field(..., description="User ID")
    action: str = Field(..., description="Action performed by the user")
    timestamp: datetime = Field(..., description="Time of the action")