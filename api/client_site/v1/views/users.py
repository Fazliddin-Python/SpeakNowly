from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Optional
from tortoise.exceptions import DoesNotExist
from models.users import User, VerificationCode
from ..serializers.users import (
    UserSerializer,
    UserCreateSerializer,
    UserUpdateSerializer,
    VerificationCodeSerializer,
)

router = APIRouter()


@router.get("/", response_model=List[UserSerializer])
async def get_users(is_active: Optional[bool] = None):
    """
    Retrieve a list of users with optional filters.
    """
    query = User.all()
    if is_active is not None:
        query = query.filter(is_active=is_active)
    users = await query.all()
    if not users:
        raise HTTPException(status_code=404, detail="No users found")
    return users


@router.get("/{user_id}/", response_model=UserSerializer)
async def get_user(user_id: int):
    """
    Retrieve a specific user by ID.
    """
    user = await User.get_or_none(id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("/", response_model=UserSerializer, status_code=status.HTTP_201_CREATED)
async def create_user(user_data: UserCreateSerializer):
    """
    Create a new user.
    """
    if await User.filter(email=user_data.email).exists():
        raise HTTPException(status_code=400, detail="Email is already registered")
    user = User(**user_data.dict())
    user.set_password(user_data.password)
    await user.save()
    return user


@router.put("/{user_id}/", response_model=UserSerializer)
async def update_user(user_id: int, user_data: UserUpdateSerializer):
    """
    Update an existing user.
    """
    user = await User.get_or_none(id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.update_from_dict(user_data.dict(exclude_unset=True))
    await user.save()
    return user


@router.delete("/{user_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int):
    """
    Delete a user by ID.
    """
    user = await User.get_or_none(id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await user.delete()
    return {"message": "User deleted successfully"}


@router.get("/verification-codes/", response_model=List[VerificationCodeSerializer])
async def get_verification_codes():
    """
    Retrieve a list of all verification codes.
    """
    codes = await VerificationCode.all()
    if not codes:
        raise HTTPException(status_code=404, detail="No verification codes found")
    return codes


@router.post("/verification-codes/", response_model=VerificationCodeSerializer, status_code=status.HTTP_201_CREATED)
async def create_verification_code(data: VerificationCodeSerializer):
    """
    Create a new verification code.
    """
    if await VerificationCode.filter(email=data.email, verification_type=data.verification_type, is_used=False).exists():
        raise HTTPException(status_code=400, detail="A verification code already exists for this email")
    code = await VerificationCode.create(**data.dict())
    return code


@router.get("/verification-codes/{code_id}/", response_model=VerificationCodeSerializer)
async def get_verification_code(code_id: int):
    """
    Retrieve a specific verification code by ID.
    """
    code = await VerificationCode.get_or_none(id=code_id)
    if not code:
        raise HTTPException(status_code=404, detail="Verification code not found")
    return code


@router.delete("/verification-codes/{code_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_verification_code(code_id: int):
    """
    Delete a verification code by ID.
    """
    code = await VerificationCode.get_or_none(id=code_id)
    if not code:
        raise HTTPException(status_code=404, detail="Verification code not found")
    await code.delete()
    return {"message": "Verification code deleted successfully"}