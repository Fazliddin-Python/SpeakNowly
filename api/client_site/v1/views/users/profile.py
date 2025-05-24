import logging
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from typing import Dict

from ...serializers.users.profile import (
    ProfileSerializer,
    ProfileUpdateSerializer,
    ProfilePasswordUpdateSerializer
)
from services.users.user_service import UserService
from utils.auth.auth import get_current_user
from utils.i18n import get_translation
from tasks.users import log_user_activity

router = APIRouter()
bearer_scheme = HTTPBearer()
logger = logging.getLogger(__name__)


@router.get(
    "/me/",
    response_model=ProfileSerializer,
    status_code=status.HTTP_200_OK
)
async def get_profile(
    current_user=Depends(get_current_user),
    t: Dict[str, str] = Depends(get_translation)
) -> ProfileSerializer:
    """
    Retrieve the current user's profile.

    Steps:
    1. Authenticate user.
    2. Return serialized profile data.
    """
    if not current_user.is_active:
        logger.warning("Inactive user tried to access profile: %s", current_user.email)
        raise HTTPException(status_code=403, detail=t["inactive_user"])

    logger.info("Profile retrieved for user: %s", current_user.email)
    return ProfileSerializer.model_validate(current_user)


@router.put(
    "/me/",
    response_model=ProfileSerializer,
    status_code=status.HTTP_200_OK
)
async def update_profile(
    data: ProfileUpdateSerializer,
    current_user=Depends(get_current_user),
    t: Dict[str, str] = Depends(get_translation)
) -> ProfileSerializer:
    """
    Update the current user's profile.

    Steps:
    1. Authenticate user.
    2. Validate and update allowed fields.
    3. Check email uniqueness if email is being updated.
    4. Save changes and return updated profile.
    5. Log activity.
    """
    if not current_user.is_active:
        logger.warning("Inactive user tried to update profile: %s", current_user.email)
        raise HTTPException(status_code=403, detail=t["inactive_user"])

    update_fields = data.dict(exclude_unset=True)
    update_fields.pop("email", None)
    for protected in ("id", "is_superuser", "tokens", "is_verified", "is_active"):
        update_fields.pop(protected, None)

    updated_user = await UserService.update_user(current_user.id, t, **update_fields)
    logger.info("Profile updated for user: %s", current_user.email)
    log_user_activity.delay(current_user.id, "profile_update")

    return ProfileSerializer.model_validate(updated_user)


@router.put(
    "/me/password/",
    status_code=status.HTTP_200_OK
)
async def update_password(
    data: ProfilePasswordUpdateSerializer,
    current_user=Depends(get_current_user),
    t: Dict[str, str] = Depends(get_translation)
) -> Dict[str, str]:
    """
    Update the current user's password.

    Steps:
    1. Authenticate user.
    2. Verify old password.
    3. Validate new password.
    4. Update password.
    5. Log activity.
    6. Return success message.
    """
    if not current_user.is_active:
        logger.warning("Inactive user tried to change password: %s", current_user.email)
        raise HTTPException(status_code=403, detail=t["inactive_user"])

    if not current_user.check_password(data.old_password):
        logger.warning("Incorrect old password for user: %s", current_user.email)
        raise HTTPException(status_code=400, detail="Incorrect old password")

    await UserService.change_password(current_user.id, data.new_password, t)
    logger.info("Password updated for user: %s", current_user.email)
    log_user_activity.delay(current_user.id, "password_update")

    return {"message": t["password_updated"]}
