from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime


class UserBaseSerializer(BaseModel):
    """
    Shared fields for User display.
    """
    email: EmailStr = Field(..., description="User's email address")
    first_name: Optional[str] = Field(None, description="User's first name")
    last_name: Optional[str] = Field(None, description="User's last name")
    age: Optional[int] = Field(None, ge=0, le=120, description="User's age (0–120)")
    photo: Optional[str] = Field(None, description="URL of the user's photo")
    is_verified: bool = Field(..., description="Whether the user is verified")
    is_active: bool = Field(..., description="Whether the user account is active")

    class Config:
        from_attributes = True


class UserCreateSerializer(BaseModel):
    """
    Schema for creating a new User (admin only).
    """
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., min_length=8, description="Password (min 8 chars)")
    first_name: Optional[str] = Field(None, description="User's first name")
    last_name: Optional[str] = Field(None, description="User's last name")
    age: Optional[int] = Field(None, ge=0, le=120, description="User's age")
    photo: Optional[str] = Field(None, description="URL of the user's photo")
    is_active: Optional[bool] = Field(True, description="Whether account is active")
    is_verified: Optional[bool] = Field(False, description="Whether email is verified")
    is_staff: Optional[bool] = Field(False, description="Grant staff privileges")
    is_superuser: Optional[bool] = Field(False, description="Grant superuser privileges")

    @validator("password")
    def validate_password_complexity(cls, v):
        if not any(c.isdigit() for c in v) or not any(c.isalpha() for c in v):
            raise ValueError("Password must contain at least one letter and one digit")
        return v

    @validator("photo")
    def validate_photo_url(cls, v):
        if v and not v.startswith(("http://", "https://")):
            raise ValueError("Photo URL must start with http:// or https://")
        return v

    class Config:
        from_attributes = True


class UserUpdateSerializer(BaseModel):
    """
    Schema for updating User fields (admin only).
    """
    email: Optional[EmailStr] = Field(None, description="Updated email")
    first_name: Optional[str] = Field(None, description="First name")
    last_name: Optional[str] = Field(None, description="Last name")
    age: Optional[int] = Field(None, ge=0, le=120, description="Age")
    photo: Optional[str] = Field(None, description="URL of the user's photo")
    is_active: Optional[bool] = Field(None, description="Activate/deactivate account")
    is_verified: Optional[bool] = Field(None, description="Verify/unverify email")
    is_staff: Optional[bool] = Field(None, description="Grant/revoke staff")
    is_superuser: Optional[bool] = Field(None, description="Grant/revoke superuser")

    @validator("photo")
    def validate_photo_url(cls, v):
        if v and not v.startswith(("http://", "https://")):
            raise ValueError("Photo URL must start with http:// or https://")
        return v

    class Config:
        from_attributes = True


class UserResponseSerializer(UserBaseSerializer):
    """
    Full User response, including read-only fields.
    """
    id: int = Field(..., description="Unique identifier")
    tokens: int = Field(..., ge=0, description="Token balance")
    is_staff: bool = Field(..., description="Whether the user is a staff member")
    is_superuser: bool = Field(..., description="Whether the user is a superuser")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")


class UserActivityLogSerializer(BaseModel):
    """
    Serializer for a single Activity Log entry.
    """
    user_id: int = Field(..., description="User ID")
    action: str = Field(..., description="Performed action")
    timestamp: datetime = Field(..., description="When the action occurred")

    class Config:
        from_attributes = True
