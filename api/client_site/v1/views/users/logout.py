import logging
from fastapi import APIRouter, Depends, status
from utils.auth.auth import get_current_user
from utils.i18n import get_translation
from tasks.users.activity_tasks import log_user_activity

router = APIRouter()
logger = logging.getLogger(__name__)

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
    2. (Optional) Invalidate token or add to blacklist.
    3. Log activity.
    4. Return 204.
    """
    logger.info("User logged out: %s", current_user.email)
    log_user_activity.delay(current_user.id, "logout")
    return