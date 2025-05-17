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
from utils.auth.auth import get_current_user
from tasks.users.activity_tasks import log_user_activity

router = APIRouter()
auth_scheme = HTTPBearer()
logger = logging.getLogger(__name__)


@router.get(
    "/",
    response_model=List[UserResponseSerializer],
    status_code=status.HTTP_200_OK
)
async def list_users(
    is_active: Optional[bool] = None,
    t: dict = Depends(get_translation),
    current_user=Depends(get_current_user)
):
    """
    List all users, optionally filtering by active status.
    Only staff or superuser can list users.
    """
    if not (current_user.is_staff or current_user.is_superuser):
        logger.warning("Permission denied for user %s to list users", current_user.email)
        raise HTTPException(status_code=403, detail="Permission denied")

    users = await UserService.list_users(is_active=is_active)
    # Always return 200 with a list (even if empty)
    return users


@router.get(
    "/{user_id}/",
    response_model=UserResponseSerializer,
    status_code=status.HTTP_200_OK
)
async def retrieve_user(
    user_id: int,
    t: dict = Depends(get_translation),
    current_user=Depends(get_current_user)
):
    """
    Retrieve a user by ID.
    Only staff or superuser can retrieve users.
    """
    if not (current_user.is_staff or current_user.is_superuser):
        logger.warning("Permission denied for user %s to retrieve user %d", current_user.email, user_id)
        raise HTTPException(status_code=403, detail="Permission denied")

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
    t: dict = Depends(get_translation),
    current_user=Depends(get_current_user)
):
    """
    Create a new user (admin only).
    """
    if not current_user.is_superuser:
        logger.warning("Permission denied for user %s to create user", current_user.email)
        raise HTTPException(status_code=403, detail="Permission denied")

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
    t: dict = Depends(get_translation),
    current_user=Depends(get_current_user)
):
    """
    Update an existing user (admin only).
    """
    if not current_user.is_superuser:
        logger.warning("Permission denied for user %s to update user %d", current_user.email, user_id)
        raise HTTPException(status_code=403, detail="Permission denied")

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
    t: dict = Depends(get_translation),
    current_user=Depends(get_current_user)
):
    """
    Delete a user by ID (admin only).
    """
    if not current_user.is_superuser:
        logger.warning("Permission denied for user %s to delete user %d", current_user.email, user_id)
        raise HTTPException(status_code=403, detail="Permission denied")

    try:
        await UserService.delete_user(user_id)
    except HTTPException as exc:
        logger.warning("User %d not found for deletion", user_id)
        raise
    logger.info("Admin deleted user %d", user_id)
    log_user_activity.delay(user_id, "admin_delete_user")
    return
