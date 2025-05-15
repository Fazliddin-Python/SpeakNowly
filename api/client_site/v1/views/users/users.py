# controllers/users/users.py

import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBearer

from ...serializers.users.users import (
    UserResponseSerializer,
    UserCreateSerializer,
    UserUpdateSerializer,
)
from services.users.user_service import UserService
from utils.i18n import get_translation
from tasks.users.activity_tasks import log_user_activity

router = APIRouter(prefix="/users", tags=["users"])
auth_scheme = HTTPBearer()
logger = logging.getLogger(__name__)


@router.get(
    "/",
    response_model=List[UserResponseSerializer],
    status_code=status.HTTP_200_OK
)
async def list_users(
    is_active: Optional[bool] = None,
    t: dict = Depends(get_translation)
):
    """
    List all users, optionally filtering by active status.
    """
    users = await UserService.list_users(is_active=is_active)
    if not users:
        logger.info("No users found with is_active=%s", is_active)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=t["users_not_found"]
        )
    return users


@router.get(
    "/{user_id}/",
    response_model=UserResponseSerializer,
    status_code=status.HTTP_200_OK
)
async def retrieve_user(
    user_id: int,
    t: dict = Depends(get_translation)
):
    """
    Retrieve a user by ID.
    """
    user = await UserService.get_by_id(user_id)
    if not user:
        logger.warning("User %d not found", user_id)
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
    t: dict = Depends(get_translation)
):
    """
    Create a new user (admin only).
    """
    exists = await UserService.get_by_email(data.email)
    if exists:
        logger.warning("Attempt to create user with existing email: %s", data.email)
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
    logger.info("Admin created user %d", user.id)
    log_user_activity.delay(user.id, "admin_create_user")
    return user


@router.put(
    "/{user_id}/",
    response_model=UserResponseSerializer,
    status_code=status.HTTP_200_OK
)
async def update_user(
    user_id: int,
    data: UserUpdateSerializer,
    t: dict = Depends(get_translation)
):
    """
    Update an existing user (admin only).
    """
    # Prevent email duplication
    if data.email:
        conflict = await UserService.get_by_email(data.email)
        if conflict and conflict.id != user_id:
            logger.warning("Email update conflict for user %d to %s", user_id, data.email)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=t["user_already_registered"]
            )

    updated = await UserService.update_user(user_id=user_id, **data.dict(exclude_none=True))
    if not updated:
        logger.warning("User %d not found for update", user_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=t["user_not_found"]
        )
    logger.info("Admin updated user %d", user_id)
    log_user_activity.delay(user_id, "admin_update_user")
    return updated


@router.delete(
    "/{user_id}/",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_user(
    user_id: int,
    t: dict = Depends(get_translation)
):
    """
    Delete a user by ID (admin only).
    """
    deleted = await UserService.delete_user(user_id)
    if not deleted:
        logger.warning("User %d not found for deletion", user_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=t["user_not_found"]
        )
    logger.info("Admin deleted user %d", user_id)
    log_user_activity.delay(user_id, "admin_delete_user")
    return
