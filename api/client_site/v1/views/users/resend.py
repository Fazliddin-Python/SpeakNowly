from fastapi import APIRouter, HTTPException, status, Depends
from redis.asyncio import Redis

from ...serializers.users import ResendOTPSchema, ResendOTPResponseSerializer
from services.users import VerificationService
from models.users import VerificationType
from utils.limiters import get_resend_limiter
from utils.i18n import get_translation
from config import REDIS_URL

router = APIRouter()

redis_client = Redis.from_url(REDIS_URL, decode_responses=True)
resend_limiter = get_resend_limiter(redis_client)

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
    key = f"{data.verification_type}:{email}"

    if await resend_limiter.is_blocked(key):
        raise HTTPException(status_code=429, detail=t["too_many_attempts"].format(minutes=5))

    await resend_limiter.register_attempt(key)

    try:
        await VerificationService.send_verification_code(
            email=email,
            verification_type=data.verification_type
        )
    except HTTPException as exc:
        detail = exc.detail if isinstance(exc.detail, str) else t["otp_resend_failed"]
        raise HTTPException(status_code=exc.status_code, detail=detail)

    return ResendOTPResponseSerializer(message=t["code_resent"])
