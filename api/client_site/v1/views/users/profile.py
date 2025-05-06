from fastapi import APIRouter, HTTPException, status, Depends
from ...serializers.users.profile import ProfileSerializer
from models.users.users import User
from utils.auth import get_current_user

router = APIRouter()

@router.put("/profile/", status_code=status.HTTP_200_OK)
async def manage_profile(
    data: ProfileSerializer,
    user_id: int = Depends(get_current_user)
):
    """
    Manage user profile: update profile, change password, or retrieve profile data.
    """
    # Fetch the user
    user = await User.get_or_none(id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Update profile fields
    if any([data.first_name, data.last_name, data.age, data.photo]):
        user.first_name = data.first_name or user.first_name
        user.last_name = data.last_name or user.last_name
        user.age = data.age if data.age is not None else user.age
        user.photo = data.photo or user.photo

    # Change password
    if data.new_password:
        if not user.check_password(data.old_password):
            raise HTTPException(status_code=400, detail="Old password is incorrect")
        if data.old_password == data.new_password:
            raise HTTPException(status_code=400, detail="New password must be different from the old password")
        user.set_password(data.new_password)

    # Save changes
    await user.save()

    # Return updated profile
    return {
        "message": "Profile updated successfully",
        "data": {
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "age": user.age,
            "photo": user.photo,
        },
    }