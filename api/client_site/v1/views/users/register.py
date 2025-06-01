import logging

from fastapi import APIRouter, HTTPException, status, Depends
from redis.asyncio import Redis

from ...serializers.users.register import RegisterSerializer, RegisterResponseSerializer
from services.users.user_service import UserService
from services.users.verification_service import VerificationService
from utils.i18n import get_translation
from models.users.verification_codes import VerificationType
from tasks.users import log_user_activity
from utils.limiters.register import RegistrationLimiter
from config import REDIS_URL

router = APIRouter()
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

    Steps:
    1. Normalize and validate email/password via serializer.
    2. Check registration rate limit (to prevent abuse).
    3. Verify that no already-verified user exists with this email.
    4. Create a new user record or reuse an unverified one.
    5. Send a verification code to the email.
    6. Register this attempt in the rate limiter.
    7. Log registration activity asynchronously.
    8. Return a simple message (no JWT tokens).
    """
    normalized_email = data.email.lower().strip()
    logger.info("Registration attempt for email: %s", normalized_email)

    # 2. Rate limit check: if blocked, reject with 429
    if await registration_limiter.is_blocked(normalized_email):
        logger.warning("Registration blocked due to too many attempts: %s", normalized_email)
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=t["too_many_attempts"])

    # 3. Check if an existing user is already verified
    existing_user = await UserService.get_by_email(normalized_email)
    if existing_user and existing_user.is_verified:
        logger.warning("Registration failed—user already verified: %s", normalized_email)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=t["user_already_registered"]
        )

    # 4. Either create a new user or reuse an unverified one
    if not existing_user:
        user = await UserService.register(email=normalized_email, password=data.password, t=t)
        first_time = True
    else:
        user = existing_user
        first_time = False

    # 5. Send verification code (verification_type=REGISTER)
    try:
        await VerificationService.send_verification_code(
            email=normalized_email,
            verification_type=VerificationType.REGISTER
        )
    except HTTPException as exc:
        logger.error("Failed to send verification code to %s: %s", normalized_email, exc.detail)
        raise  # Propagate the HTTPException from the service

    # 6. Register this (failed) attempt for limiter purposes
    await registration_limiter.register_failed_attempt(normalized_email)

    # 7. Asynchronously log registration activity
    log_user_activity.delay(user.id, "register")
    logger.info("Verification code dispatched to %s; user record ID %s", normalized_email, user.id)

    # 8. Return message only (no tokens at this stage)
    message_key = "verification_sent" if first_time else "verification_resent"
    return RegisterResponseSerializer(message=t[message_key])
