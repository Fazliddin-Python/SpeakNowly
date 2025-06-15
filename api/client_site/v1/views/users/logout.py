from fastapi import APIRouter, Depends, status
from tasks.users import log_user_activity
from utils.auth import get_current_user
from utils.i18n import get_translation

router = APIRouter()

@router.post(
    "/logout/",
    status_code=status.HTTP_204_NO_CONTENT
)
async def logout(
    current_user=Depends(get_current_user),
    t: dict = Depends(get_translation)
):
    """
    Log out the current user.

    Steps:
    1. Authenticate user.
    2. Log activity.
    3. Return 204.
    """
    await log_user_activity.delay(current_user.id, "logout")
    return {"message": t["logout_successful"]}