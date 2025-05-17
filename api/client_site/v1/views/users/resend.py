import logging

from fastapi import APIRouter, HTTPException, status, Depends
from redis.asyncio import Redis

from ...serializers.users.resend import ResendOTPSchema, ResendOTPResponseSerializer
from services.users.verification_service import VerificationService
from utils.limiters.resend import ResendLimiter
from utils.i18n import get_translation
from models.users.verification_codes import VerificationType
from config import REDIS_URL

router = APIRouter()
logger = logging.getLogger(__name__)

redis_client = Redis.from_url(REDIS_URL, decode_responses=True)
resend_limiter = ResendLimiter(redis_client)


@router.post(
    "/resend-otp/",
    response_model=ResendOTPResponseSerializer,
    status_code=status.HTTP_202_ACCEPTED
)
async def resend_otp(
    data: ResendOTPSchema,
    t: dict = Depends(get_translation)
) -> ResendOTPResponseSerializer:
    """
    Resend an OTP code to user email.

    Steps:
    1. Normalize and validate input.
    2. Check resend rate limit.
    3. Register resend attempt for limiter.
    4. Send verification code using VerificationService.
    5. Return response.
    """
    email = data.email.lower().strip()
    verification_type = data.verification_type
    logger.info("Resend OTP requested for %s type=%s", email, verification_type)

    # 2. Rate-limit check
    if await resend_limiter.is_blocked(email, verification_type):
        logger.warning("Resend OTP blocked due to too many attempts: %s type=%s", email, verification_type)
        raise HTTPException(status_code=429, detail=t["too_many_attempts"])

    # 3. Register resend attempt for limiter
    await resend_limiter.register_attempt(email, verification_type)

    # 4. Send OTP
    try:
        await VerificationService.send_verification_code(
            email=email,
            verification_type=verification_type
        )
    except HTTPException as exc:
        detail = exc.detail if isinstance(exc.detail, str) else t["otp_resend_failed"]
        logger.warning("Resend OTP failed for %s: %s", email, detail)
        raise HTTPException(status_code=exc.status_code, detail=detail)

    logger.info("OTP resent to %s type=%s", email, verification_type)
    return ResendOTPResponseSerializer(message=t["code_resent"])
