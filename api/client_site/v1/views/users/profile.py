import aiofiles
import pathlib
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from typing import Dict
from uuid import uuid4

from ...serializers.users import ProfileSerializer, ProfilePasswordUpdateSerializer
from services.users import UserService
from tasks.users import log_user_activity
from utils.auth import get_current_user
from utils.i18n import get_translation

router = APIRouter()


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
    Get the current user's profile.

    Steps:
    1. Check user is active.
    2. Fetch related tariff.
    3. Return serialized profile.
    """
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=t["inactive_user"])

    await current_user.fetch_related("tariff")

    return ProfileSerializer(
        email=current_user.email,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        age=current_user.age,
        photo=current_user.photo,
        tokens=current_user.tokens,
        is_premium=current_user.is_premium
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
    1. Check user is active.
    2. Collect update fields.
    3. Save photo to /media/ asynchronously if provided.
    4. Update user in DB.
    5. Fetch related tariff.
    6. Log activity.
    7. Return updated profile.
    """
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=t["inactive_user"])

    update_fields = {}
    if first_name is not None:
        update_fields["first_name"] = first_name
    if last_name is not None:
        update_fields["last_name"] = last_name
    if age is not None:
        update_fields["age"] = age

    if photo is not None:
        if photo.content_type not in ("image/jpeg", "image/png", "image/gif"):
            raise HTTPException(status_code=400, detail="Invalid image type")
        file_ext = photo.filename.split('.')[-1]
        project_root = pathlib.Path(__file__).resolve().parents[5]
        save_dir = project_root / "media" / "user_photos" / str(current_user.id)
        save_dir.mkdir(parents=True, exist_ok=True)
        file_name = f"{uuid4()}.{file_ext}"
        file_path = save_dir / file_name
        file_content = await photo.read()
        if not file_content:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(file_content)
        photo_url = f"/media/user_photos/{current_user.id}/{file_name}"
        update_fields["photo"] = photo_url

    updated_user = await UserService.update_user(current_user.id, t, **update_fields)

    await updated_user.fetch_related("tariff")
    await log_user_activity.delay(current_user.id, "profile_update")

    return ProfileSerializer(
        email=updated_user.email,
        first_name=updated_user.first_name,
        last_name=updated_user.last_name,
        age=updated_user.age,
        photo=updated_user.photo,
        tokens=updated_user.tokens,
        is_premium=updated_user.is_premium
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
    Change the current user's password.

    Steps:
    1. Check user is active.
    2. Verify old password.
    3. Change password in DB.
    4. Log activity.
    5. Return success message.
    """
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=t["inactive_user"])

    if not current_user.check_password(data.old_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect old password")

    await UserService.change_password(current_user.id, data.new_password, t)
    await log_user_activity.delay(current_user.id, "password_update")

    return {"message": t["password_updated"]}