from pydantic import BaseModel, EmailStr
from typing import Optional

class UserSerializer(BaseModel):
    id: int
    email: EmailStr
    age: Optional[int]
    is_verified: bool
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


class UserUpdateSerializer(BaseModel):
    email: Optional[EmailStr]
    age: Optional[int]
    is_active: Optional[bool]
    is_staff: Optional[bool]
    is_superuser: Optional[bool]


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