import logging

from fastapi import APIRouter, HTTPException, status, Depends
from redis.asyncio import Redis

from ...serializers.users.forget_password import ForgetPasswordSerializer, ResetPasswordSerializer
from services.users.verification_service import VerificationService
from services.users.user_service import UserService
from utils.limiters import get_forget_password_limiter
from utils.i18n import get_translation
from tasks.users import log_user_activity
from models.users.verification_codes import VerificationType
from config import REDIS_URL

router = APIRouter()
logger = logging.getLogger(__name__)

redis_client = Redis.from_url(REDIS_URL, decode_responses=True)
forget_password_limiter = get_forget_password_limiter(redis_client)


@router.post("/forget-password/", status_code=status.HTTP_200_OK)
async def request_password_reset(
    data: ForgetPasswordSerializer,
    t: dict = Depends(get_translation)
):
    """
    Step 1: Request a password reset.
    1. Check if user exists and is active.
    2. Check rate limit.
    3. Register failed attempt for limiter.
    4. Send verification code.
    5. Log activity.
    6. Return response.
    """
    normalized_email = data.email.lower().strip()
    logger.info("Password reset requested for email: %s", normalized_email)

    # 1. Check if user exists and is active
    user = await UserService.get_by_email(normalized_email)
    if not user or not user.is_active:
        logger.warning("Password reset failed: user not found or inactive (%s)", normalized_email)
        raise HTTPException(status_code=404, detail=t["user_not_found"])

    # 2. Rate-limit check
    if await forget_password_limiter.is_blocked(normalized_email):
        logger.warning("Password reset blocked due to too many attempts: %s", normalized_email)
        raise HTTPException(status_code=429, detail=t["too_many_attempts"])

    # 3. Register failed attempt for limiter
    await forget_password_limiter.register_attempt(normalized_email)

    # 4. Send verification code
    try:
        await VerificationService.send_verification_code(
            email=normalized_email,
            verification_type=VerificationType.FORGET_PASSWORD
        )
    except HTTPException as exc:
        detail = exc.detail if isinstance(exc.detail, str) else t["otp_resend_failed"]
        logger.warning("Failed to send password-reset OTP to %s: %s", normalized_email, detail)
        raise HTTPException(status_code=exc.status_code, detail=detail)

    # 5. Log activity
    log_user_activity.delay(user.id, "forget_password_request")

    # 6. Return response
    return {"message": t["verification_sent"]}


@router.post("/forget-password/confirm/", status_code=status.HTTP_200_OK)
async def confirm_password_reset(
    data: ResetPasswordSerializer,
    t: dict = Depends(get_translation)
):
    """
    Step 2: Confirm the OTP and set a new password.
    1. Verify OTP using VerificationService.
    2. Reset limiter on success.
    3. Change password using UserService.
    4. Delete unused codes.
    5. Log activity.
    6. Return response.
    """
    normalized_email = data.email.lower().strip()
    logger.info("Confirming password reset: email=%s code=%s", normalized_email, data.code)

    # 1. Verify OTP
    try:
        user = await VerificationService.verify_code(
            email=normalized_email,
            code=str(data.code),
            verification_type=VerificationType.FORGET_PASSWORD
        )
    except HTTPException as exc:
        detail = exc.detail if isinstance(exc.detail, str) else t["otp_verification_failed"]
        logger.warning("Password reset verification failed for %s: %s", normalized_email, detail)
        raise HTTPException(status_code=exc.status_code, detail=detail)

    # 2. Reset limiter on success
    await forget_password_limiter.reset_attempts(normalized_email)

    # 3. Change password
    await UserService.change_password(user.id, data.new_password, t)

    # 4. Delete unused codes
    await VerificationService.delete_unused_codes(
        email=normalized_email,
        verification_type=VerificationType.FORGET_PASSWORD
    )

    # 5. Log activity
    log_user_activity.delay(user.id, "forget_password_confirm")

    # 6. Return response
    return {"message": t["password_updated"]}
