from fastapi import APIRouter, HTTPException, status
from ..serializers.profile_update import ProfileUpdateSerializer

router = APIRouter()


@router.put("/profile/", status_code=status.HTTP_200_OK)
async def update_profile(user_id: int, data: ProfileUpdateSerializer):
    """
    Update user profile information.
    """
    user = await User.get_or_none(id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.update_from_dict(data.dict(exclude_unset=True))
    await user.save()
    return {"message": "Profile updated successfully"}