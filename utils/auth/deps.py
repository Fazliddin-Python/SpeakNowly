import logging
from fastapi import Depends, HTTPException, status, Request
from utils.auth.auth import get_current_user
from utils.i18n import get_translation

logger = logging.getLogger(__name__)

def audit_action(action: str):
    """
    Dependency factory: logs user action and returns the user object.
    """
    async def wrapper(request: Request, user=Depends(get_current_user)):
        logger.info(f"User {user.id} action='{action}' path='{request.url.path}'")
        return user
    return wrapper

async def active_user(user=Depends(get_current_user), t=Depends(get_translation)):
    """
    Ensures the user is active.
    """
    if not user.is_active:
        logger.warning(f"Inactive user (id={user.id}) attempted access")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=t["inactive_user"])
    return user

async def admin_required(user=Depends(get_current_user), t=Depends(get_translation)):
    """
    Ensures the user has admin privileges.
    """
    if not (user.is_staff and user.is_superuser):
        logger.warning(f"Permission denied for user_id={user.id}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=t["permission_denied"])
    return user