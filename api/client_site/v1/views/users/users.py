from fastapi import APIRouter, HTTPException, status
from typing import List, Optional
from models.users.users import User
from ...serializers.users.users import (
    UserBaseSerializer,
    UserCreateSerializer,
    UserUpdateSerializer,
)

router = APIRouter()

# Users
@router.get("/", response_model=List[UserBaseSerializer])
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


@router.get("/{user_id}/", response_model=UserBaseSerializer)
async def get_user(user_id: int):
    """
    Retrieve a specific user by ID.
    """
    user = await User.get_or_none(id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("/", response_model=UserBaseSerializer, status_code=status.HTTP_201_CREATED)
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


@router.put("/{user_id}/", response_model=UserBaseSerializer)
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