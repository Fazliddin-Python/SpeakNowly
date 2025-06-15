from fastapi import APIRouter, HTTPException, status, Depends
from redis.asyncio import Redis

from ...serializers.users import RegisterSerializer, RegisterResponseSerializer
from services.users import VerificationService, UserService
from tasks.users import log_user_activity
from models.users import VerificationType
from utils.limiters import get_register_limiter
from utils.i18n import get_translation
from config import REDIS_URL

router = APIRouter()

redis_client = Redis.from_url(REDIS_URL, decode_responses=True)
register_limiter = get_register_limiter(redis_client)


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
    Register a new user and send verification code.

    Steps:
    1. Normalize email.
    2. Check registration rate limit.
    3. Check if user already exists and is verified.
    4. Create new user or reuse unverified one.
    5. Send verification code.
    6. Register attempt in limiter.
    7. Log registration activity.
    8. Return response.
    """
    email = data.email.lower().strip()

    if await register_limiter.is_blocked(email):
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=t["too_many_attempts"].format(minutes=10))

    existing_user = await UserService.get_by_email(email)
    if existing_user and existing_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=t["user_already_registered"]
        )

    if not existing_user:
        user = await UserService.register(email=email, password=data.password, t=t)
        first_time = True
    else:
        user = existing_user
        first_time = False

    try:
        await VerificationService.send_verification_code(
            email=email,
            verification_type=VerificationType.REGISTER
        )
    except HTTPException as exc:
        raise  # Propagate the HTTPException from the service

    await register_limiter.register_attempt(email)
    await log_user_activity.delay(user.id, "register")

    message_key = "verification_sent" if first_time else "verification_resent"
    return RegisterResponseSerializer(message=t[message_key])
