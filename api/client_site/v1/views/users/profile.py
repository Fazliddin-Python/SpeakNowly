import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.security import HTTPBearer
from typing import Dict
from minio import Minio
from uuid import uuid4
from io import BytesIO

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

MINIO_BUCKET = "user-photo"
minio_client = Minio(
    # "136.243.2.242:9000",
    "localhost:9000",
    access_key="minioadmin",
    secret_key="minioadmin123",
    secure=False
)

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
    2. Fetch related tariff to determine premium status.
    3. Return serialized profile data with tokens and is_premium.
    """
    if not current_user.is_active:
        logger.warning("Inactive user tried to access profile: %s", current_user.email)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=t["inactive_user"])

    # Ensure tariff relationship is loaded before checking is_premium
    await current_user.fetch_related("tariff")

    tokens_balance = current_user.tokens
    is_premium = current_user.is_premium

    logger.info("Profile retrieved for user: %s", current_user.email)
    return ProfileSerializer(
        email=current_user.email,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        age=current_user.age,
        photo=current_user.photo,
        tokens=tokens_balance,
        is_premium=is_premium
    )


@router.put(
    "/me/",
    response_model=ProfileSerializer,
    status_code=status.HTTP_200_OK
)
async def update_profile(
    first_name: str = Form(None),
    last_name: str = Form(None),
    age: int = Form(None),
    photo: UploadFile = File(None),
    current_user=Depends(get_current_user),
    t: Dict[str, str] = Depends(get_translation)
) -> ProfileSerializer:
    """
    Update the current user's profile.

    Steps:
    1. Authenticate user.
    2. Validate and update allowed fields.
    3. Save changes.
    4. Fetch related tariff to determine premium status.
    5. Log activity.
    6. Return updated profile with tokens and is_premium.
    """
    if not current_user.is_active:
        logger.warning("Inactive user tried to update profile: %s", current_user.email)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=t["inactive_user"])

    update_fields = {}
    if first_name is not None:
        update_fields["first_name"] = first_name
    if last_name is not None:
        update_fields["last_name"] = last_name
    if age is not None:
        update_fields["age"] = age

    # Обработка фото через MinIO
    if photo is not None:
        if photo.content_type not in ("image/jpeg", "image/png", "image/gif"):
            raise HTTPException(status_code=400, detail="Invalid image type")
        file_ext = photo.filename.split('.')[-1]
        file_name = f"profile_photos/{current_user.id}/{uuid4()}.{file_ext}"
        file_content = await photo.read()
        try:
            minio_client.put_object(
                bucket_name=MINIO_BUCKET,
                object_name=file_name,
                data=BytesIO(file_content),
                length=len(file_content),
                content_type=photo.content_type,
            )
        except Exception as e:
            logger.error("MinIO upload error: %s", e)
            raise HTTPException(status_code=500, detail="Failed to upload image")
        photo_url = f"https://api.speaknowly.com/minio-console/browser/user-photo/{file_name}"
        update_fields["photo"] = photo_url

    updated_user = await UserService.update_user(current_user.id, t, **update_fields)
    logger.info("Profile updated for user: %s", current_user.email)
    log_user_activity.delay(current_user.id, "profile_update")

    # Ensure tariff relationship is loaded before checking is_premium
    await updated_user.fetch_related("tariff")
    tokens_balance = updated_user.tokens
    is_premium = updated_user.is_premium

    return ProfileSerializer(
        email=updated_user.email,
        first_name=updated_user.first_name,
        last_name=updated_user.last_name,
        age=updated_user.age,
        photo=updated_user.photo,
        tokens=tokens_balance,
        is_premium=is_premium
    )


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
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=t["inactive_user"])

    if not current_user.check_password(data.old_password):
        logger.warning("Incorrect old password for user: %s", current_user.email)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect old password")

    await UserService.change_password(current_user.id, data.new_password, t)
    logger.info("Password updated for user: %s", current_user.email)
    log_user_activity.delay(current_user.id, "password_update")

    return {"message": t["password_updated"]}
