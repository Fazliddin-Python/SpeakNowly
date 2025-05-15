import logging

from fastapi import APIRouter, HTTPException, status, Depends
from redis.asyncio import Redis

from ...serializers.users.register import RegisterSerializer, RegisterResponseSerializer
from services.users.user_service import UserService
from services.users.verification_service import VerificationService
from utils.auth.auth import create_access_token
from utils.i18n import get_translation
from models.users.verification_codes import VerificationType
from tasks.users.activity_tasks import log_user_activity
from utils.limiters.register import RegistrationLimiter
from config import REDIS_URL

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger(__name__)

redis_client = Redis.from_url(REDIS_URL, decode_responses=True)
registration_limiter = RegistrationLimiter(redis_client)


@router.post(
    "/register/",
    response_model=RegisterResponseSerializer,
    status_code=status.HTTP_201_CREATED
)
async def register(
    data: RegisterSerializer,
    t: dict = Depends(get_translation)
) -> RegisterResponseSerializer:
    """
    Handle user registration and send verification code.
    """
    normalized_email = data.email.lower().strip()
    logger.info("Registration attempt for email: %s", normalized_email)

    # 1. Rate limit check (block repeated abuse)
    if await registration_limiter.is_blocked(normalized_email):
        logger.warning("Registration blocked due to too many attempts: %s", normalized_email)
        raise HTTPException(status_code=429, detail=t["too_many_attempts"])

    # 2. Check existing user
    existing = await UserService.get_by_email(normalized_email)
    if existing and existing.is_verified:
        logger.warning("Registration failed, user already verified: %s", normalized_email)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=t["user_already_registered"]
        )

    # 3. Create new user or reuse unverified one
    if not existing:
        user = await UserService.register(email=normalized_email, password=data.password)
        first_time = True
    else:
        user = existing
        first_time = False

    # 4. Send verification code (internal to service)
    try:
        await VerificationService.send_verification_code(
            email=normalized_email,
            verification_type=VerificationType.REGISTER
        )
    except HTTPException as exc:
        logger.error("Failed to send registration code: %s", exc.detail)
        raise

    # 5. Register failed attempt for limiter
    await registration_limiter.register_failed_attempt(normalized_email)

    # 6. Issue JWT and response
    token = create_access_token(subject=str(user.id), email=user.email)
    msg_key = "verification_sent" if first_time else "verification_resent"
    logger.info("Verification code sent to %s; JWT issued", normalized_email)

    # 7. Log activity asynchronously
    log_user_activity.delay(user.id, "register")

    return RegisterResponseSerializer(message=t[msg_key], token=token)
