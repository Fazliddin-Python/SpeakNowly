import logging

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBearer

from ...serializers.users.profile import (
    ProfileSerializer,
    ProfileUpdateSerializer,
    ProfilePasswordUpdateSerializer,
)
from services.users.user_service import UserService
from utils.auth.auth import get_current_user
from utils.i18n import get_translation
from tasks.users.activity_tasks import log_user_activity

router = APIRouter(prefix="/profile", tags=["profile"])
bearer_scheme = HTTPBearer()
logger = logging.getLogger(__name__)


@router.get("/", response_model=ProfileSerializer)
async def get_profile(
    current: dict = Depends(get_current_user),
    t: dict = Depends(get_translation)
) -> ProfileSerializer:
    user = await UserService.get_by_id(current["user_id"])
    if not user:
        logger.warning("Profile retrieval failed: user %s not found", current["user_id"])
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=t["user_not_found"])

    log_user_activity.delay(user.id, "view_profile")
    logger.info("Profile retrieved for user %s", user.id)
    return ProfileSerializer.from_orm(user)


@router.get("/{user_id}", response_model=ProfileSerializer)
async def get_user_profile(
    user_id: int,
    t: dict = Depends(get_translation)
) -> ProfileSerializer:
    user = await UserService.get_by_id(user_id)
    if not user:
        logger.warning("Profile retrieval failed: user %s not found", user_id)
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=t["user_not_found"])
    return ProfileSerializer.from_orm(user)


@router.put("/", response_model=ProfileSerializer)
async def update_profile(
    data: ProfileUpdateSerializer,
    current: dict = Depends(get_current_user),
    t: dict = Depends(get_translation)
) -> ProfileSerializer:
    user_id = current["user_id"]
    user = await UserService.get_by_id(user_id)
    if not user:
        logger.warning("Profile update failed: user %s not found", user_id)
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=t["user_not_found"])

    if data.email and data.email != user.email:
        exists = await UserService.get_by_email(data.email)
        if exists:
            logger.warning("Email update failed: %s already in use", data.email)
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=t["email_already_in_use"])

    updated = await UserService.update_user(
        user_id=user_id, **data.dict(exclude_unset=True)
    )
    log_user_activity.delay(user_id, "update_profile")
    logger.info("Profile updated for user %s", user_id)
    return ProfileSerializer.from_orm(updated)


@router.put("/password", status_code=status.HTTP_200_OK)
async def update_password(
    data: ProfilePasswordUpdateSerializer,
    current: dict = Depends(get_current_user),
    t: dict = Depends(get_translation)
) -> dict:
    user_id = current["user_id"]
    user = await UserService.get_by_id(user_id)
    if not user:
        logger.warning("Password update failed: user %s not found", user_id)
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=t["user_not_found"])

    if not user.check_password(data.old_password):
        logger.warning("Password update failed for user %s: incorrect old password", user_id)
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=t["incorrect_password"])

    if data.old_password == data.new_password:
        logger.warning("Password update failed for user %s: new password same as old", user_id)
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=t["password_must_differ"])

    await UserService.change_password(user_id, data.new_password)
    log_user_activity.delay(user_id, "update_password")
    logger.info("Password updated for user %s", user_id)

    return {"message": t["password_updated"]}
