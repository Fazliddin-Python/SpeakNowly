from pydantic import BaseModel, EmailStr
from typing import Optional


class UserSerializer(BaseModel):
    id: int
    telegram_id: Optional[int]
    email: EmailStr
    age: Optional[int]
    is_verified: bool
    photo: Optional[str]
    tariff_id: Optional[int]
    tokens: int
    is_active: bool
    is_staff: bool
    is_superuser: bool
    last_login: Optional[str]

    class Config:
        from_attributes = True


class UserCreateSerializer(BaseModel):
    email: EmailStr
    password: str
    age: Optional[int]
    telegram_id: Optional[int]

    class Config:
        from_attributes = True


class UserUpdateSerializer(BaseModel):
    email: Optional[EmailStr]
    age: Optional[int]
    is_active: Optional[bool]
    is_staff: Optional[bool]
    is_superuser: Optional[bool]
    photo: Optional[str]

    class Config:
        from_attributes = True


class VerificationCodeSerializer(BaseModel):
    id: int
    email: Optional[EmailStr]
    user_id: Optional[int]
    verification_type: str
    code: int
    is_used: bool
    is_expired: bool

    class Config:
        from_attributes = True


class UserActivityLogSerializer(BaseModel):
    id: int
    user_id: int
    action: str
    timestamp: str

    class Config:
        from_attributes = True