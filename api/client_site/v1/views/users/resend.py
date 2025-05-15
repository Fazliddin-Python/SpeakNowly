import logging

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBearer
from redis.asyncio import Redis

from ...serializers.users.resend import ResendSerializer
from services.users.verification_service import VerificationService
from services.users.user_service import UserService
from utils.i18n import get_translation
from tasks.users.activity_tasks import log_user_activity
from models.users.verification_codes import VerificationType
from utils.limiters.resend import ResendLimiter
from config import REDIS_URL

router = APIRouter(prefix="/auth", tags=["auth"])
bearer = HTTPBearer()
logger = logging.getLogger(__name__)

redis_client = Redis.from_url(REDIS_URL, decode_responses=True)
resend_limiter = ResendLimiter(redis_client)


@router.post("/resend/", status_code=status.HTTP_200_OK)
async def resend_verification_code(
    data: ResendSerializer,
    t: dict = Depends(get_translation)
):
    """
    Resend a verification code to the specified email address.
    Supports contexts: REGISTER (no user required), FORGET_PASSWORD, UPDATE_EMAIL (user must exist).
    """
    logger.info("Resend OTP for %s type=%s", data.email, data.verification_type)

    # 1. Rate-limit check
    if await resend_limiter.is_blocked(data.email, data.verification_type.value):
        logger.warning("Too many resend attempts for %s (%s)", data.email, data.verification_type)
        raise HTTPException(status_code=429, detail=t["too_many_attempts"])

    # 2. Enforce user presence if required
    user = None
    if data.verification_type in {VerificationType.FORGET_PASSWORD, VerificationType.UPDATE_EMAIL}:
        user = await UserService.get_by_email(data.email)
        if not user:
            logger.warning("Resend OTP failed: user not found for %s", data.email)
            raise HTTPException(status_code=404, detail=t["user_not_found"])
    elif data.verification_type == VerificationType.REGISTER:
        logger.info("Resend OTP for registration: %s", data.email)

    # 3. Register current attempt
    await resend_limiter.register_attempt(data.email, data.verification_type.value)

    # 4. Generate and send verification code
    try:
        code = await VerificationService.send_verification_code(
            email=data.email,
            verification_type=data.verification_type
        )
    except HTTPException as exc:
        detail = exc.detail if isinstance(exc.detail, str) else t["otp_resend_failed"]
        logger.warning("Resend OTP error: %s", detail)
        raise HTTPException(status_code=exc.status_code, detail=detail)

    log_user_activity.delay(user.id if user else 0, f"resend_{data.verification_type}")
    return {"message": t["code_resent"]}
