from fastapi import APIRouter, HTTPException, status, Depends
from redis.asyncio import Redis

from ...serializers.users import ForgetPasswordSerializer, ResetPasswordSerializer
from services.users import VerificationService, UserService
from tasks.users import log_user_activity
from models.users import VerificationType
from utils.limiters import get_forget_password_limiter
from utils.i18n import get_translation
from config import REDIS_URL

router = APIRouter()

redis_client = Redis.from_url(REDIS_URL, decode_responses=True)
forget_password_limiter = get_forget_password_limiter(redis_client)

@router.post("/forget-password/", status_code=status.HTTP_200_OK)
async def request_password_reset(
    data: ForgetPasswordSerializer,
    t: dict = Depends(get_translation)
):
    """
    Request a password reset.

    Steps:
    1. Check if user exists and is active.
    2. Check rate limit.
    3. Register attempt for limiter.
    4. Send verification code.
    5. Log activity.
    6. Return response.
    """
    normalized_email = data.email.lower().strip()

    user = await UserService.get_by_email(normalized_email)
    if not user or not user.is_active:
        raise HTTPException(status_code=404, detail=t["user_not_found"])

    if await forget_password_limiter.is_blocked(normalized_email):
        raise HTTPException(status_code=429, detail=t["too_many_attempts"].format(minutes=15))

    await forget_password_limiter.register_attempt(normalized_email)

    try:
        await VerificationService.send_verification_code(
            email=normalized_email,
            verification_type=VerificationType.FORGET_PASSWORD
        )
    except HTTPException as exc:
        detail = exc.detail if isinstance(exc.detail, str) else t["otp_resend_failed"]
        raise HTTPException(status_code=exc.status_code, detail=detail)

    await log_user_activity.delay(user.id, "forget_password_request")

    return {"message": t["verification_sent"]}


@router.post("/forget-password/confirm/", status_code=status.HTTP_200_OK)
async def confirm_password_reset(
    data: ResetPasswordSerializer,
    t: dict = Depends(get_translation)
):
    """
    Confirm the OTP and set a new password.

    Steps:
    1. Verify OTP using VerificationService.
    2. Reset limiter on success.
    3. Change password using UserService.
    4. Delete unused codes.
    5. Log activity.
    6. Return response.
    """
    normalized_email = data.email.lower().strip()

    try:
        user = await VerificationService.verify_code(
            email=normalized_email,
            code=str(data.code),
            verification_type=VerificationType.FORGET_PASSWORD
        )
    except HTTPException as exc:
        detail = exc.detail if isinstance(exc.detail, str) else t["otp_verification_failed"]
        raise HTTPException(status_code=exc.status_code, detail=detail)

    await forget_password_limiter.reset_attempts(normalized_email)
    await UserService.change_password(user.id, data.new_password, t)
    await VerificationService.delete_unused_codes(
        email=normalized_email,
        verification_type=VerificationType.FORGET_PASSWORD
    )
    await log_user_activity.delay(user.id, "forget_password_confirm")

    return {"message": t["password_updated"]}
