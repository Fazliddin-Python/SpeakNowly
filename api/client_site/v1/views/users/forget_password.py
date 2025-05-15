import logging

from fastapi import APIRouter, HTTPException, status, Depends
from redis.asyncio import Redis

from ...serializers.users.forget_password import ForgetPasswordSerializer, ResetPasswordSerializer
from services.users.verification_service import VerificationService
from services.users.user_service import UserService
from utils.limiters.forget_password import ForgetPasswordLimiter
from utils.i18n import get_translation
from tasks.users.activity_tasks import log_user_activity
from models.users.verification_codes import VerificationType
from config import REDIS_URL

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger(__name__)

redis_client = Redis.from_url(REDIS_URL, decode_responses=True)
forget_limiter = ForgetPasswordLimiter(redis_client)


@router.post("/forget-password/", status_code=status.HTTP_200_OK)
async def request_password_reset(
    data: ForgetPasswordSerializer,
    t: dict = Depends(get_translation)
):
    """
    Step 1: Request a password reset.
    Sends an OTP to the user's email.
    """
    logger.info("Password reset requested for email: %s", data.email)

    user = await UserService.get_by_email(data.email)
    if not user:
        logger.warning("Password reset failed: user not found (%s)", data.email)
        raise HTTPException(status_code=404, detail=t["user_not_found"])
    if not user.is_active:
        logger.warning("Password reset failed: user is inactive (%s)", data.email)
        raise HTTPException(status_code=403, detail=t["inactive_user"])

    # 1. Rate-limit check
    if await forget_limiter.is_blocked(data.email):
        logger.warning("Password reset blocked due to too many attempts: %s", data.email)
        raise HTTPException(status_code=429, detail=t["too_many_requests"])

    # 2. Increment attempt counter
    await forget_limiter.increment_attempts(data.email)

    # 3. Send verification code
    try:
        await VerificationService.send_verification_code(
            email=data.email,
            verification_type=VerificationType.FORGET_PASSWORD
        )
    except HTTPException as exc:
        detail = exc.detail if isinstance(exc.detail, str) else t["otp_resend_failed"]
        logger.warning("Failed to send password-reset OTP to %s: %s", data.email, detail)
        raise HTTPException(status_code=exc.status_code, detail=detail)

    # 4. Log activity
    log_user_activity.delay(user.id, "forget_password_request")
    return {"message": t["verification_sent"]}


@router.post("/forget-password/confirm/", status_code=status.HTTP_200_OK)
async def confirm_password_reset(
    data: ResetPasswordSerializer,
    t: dict = Depends(get_translation)
):
    """
    Step 2: Confirm the OTP and set a new password.
    Verifies the code, updates the password, and cleans up OTPs.
    """
    logger.info("Confirming password reset: email=%s code=%s", data.email, data.code)

    try:
        user = await VerificationService.verify_code(
            email=data.email,
            code=data.code,
            verification_type=VerificationType.FORGET_PASSWORD
        )
    except HTTPException as exc:
        detail = exc.detail if isinstance(exc.detail, str) else t["otp_verification_failed"]
        logger.warning("Password reset verification failed for %s: %s", data.email, detail)
        raise HTTPException(status_code=exc.status_code, detail=detail)

    # 5. On successful verification — reset limiter
    await forget_limiter.reset_attempts(data.email)

    # 6. Change password
    await UserService.change_password(user.id, data.new_password)

    # 7. Cleanup any unused codes
    await VerificationService.delete_unused_codes(
        email=data.email,
        verification_type=VerificationType.FORGET_PASSWORD
    )

    log_user_activity.delay(user.id, "forget_password_confirm")
    return {"message": t["password_updated"]}
