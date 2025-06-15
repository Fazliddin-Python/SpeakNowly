from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Optional

from ...serializers.users import UserResponseSerializer, UserCreateSerializer, UserUpdateSerializer
from services.users import UserService
from tasks.users import log_user_activity
from utils.auth import admin_required
from utils.i18n import get_translation

router = APIRouter()


@router.get(
    "/",
    response_model=List[UserResponseSerializer],
    status_code=status.HTTP_200_OK
)
async def list_users(
    is_active: Optional[bool] = None,
    t: dict = Depends(get_translation),
    current_user=Depends(admin_required)
):
    """
    List all users, optionally filtering by active status.
    Only staff or superuser can list users.
    """
    users = await UserService.list_users(is_active=is_active)
    return users


@router.get(
    "/{user_id}/",
    response_model=UserResponseSerializer,
    status_code=status.HTTP_200_OK
)
async def retrieve_user(
    user_id: int,
    t: dict = Depends(get_translation),
    current_user=Depends(admin_required)
):
    """
    Retrieve a user by ID.
    Only staff or superuser can retrieve users.
    """
    user = await UserService.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=t["user_not_found"]
        )
    return user


@router.post(
    "/",
    response_model=UserResponseSerializer,
    status_code=status.HTTP_201_CREATED
)
async def create_user(
    data: UserCreateSerializer,
    t: dict = Depends(get_translation),
    current_user=Depends(admin_required)
):
    """
    Create a new user (admin only).
    """
    exists = await UserService.get_by_email(data.email)
    if exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=t["user_already_registered"]
        )

    user = await UserService.create_user(
        email=data.email,
        password=data.password,
        first_name=data.first_name,
        last_name=data.last_name,
        age=data.age,
        photo=data.photo,
        is_active=data.is_active,
        is_verified=data.is_verified,
        is_staff=data.is_staff,
        is_superuser=data.is_superuser
    )
    await log_user_activity.delay(user.id, "admin_create_user")
    return user


@router.put(
    "/{user_id}/",
    response_model=UserResponseSerializer,
    status_code=status.HTTP_200_OK
)
async def update_user(
    user_id: int,
    data: UserUpdateSerializer,
    t: dict = Depends(get_translation),
    current_user=Depends(admin_required)
):
    """
    Update an existing user (admin only).
    """
    if data.email:
        conflict = await UserService.get_by_email(data.email)
        if conflict and conflict.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=t["user_already_registered"]
            )

    updated = await UserService.admin_update_user(user_id=user_id, t=t, **data.dict(exclude_none=True))
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=t["user_not_found"]
        )
    await log_user_activity.delay(user_id, "admin_update_user")
    return updated


@router.delete(
    "/{user_id}/",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_user(
    user_id: int,
    t: dict = Depends(get_translation),
    current_user=Depends(admin_required)
):
    """
    Delete a user by ID (admin only).
    """
    await UserService.delete_user(user_id, t)
    await log_user_activity.delay(user_id, "admin_delete_user")
    return
