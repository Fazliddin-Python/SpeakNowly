import logging

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBearer
from redis.asyncio import Redis

from ...serializers.users.login import LoginSerializer, OAuth2SignInSerializer, AuthResponseSerializer
from services.users.user_service import UserService
from utils.auth.auth import create_access_token, decode_access_token
from utils.auth.oauth2_auth import oauth2_sign_in
from utils.i18n import get_translation
from tasks.users.activity_tasks import log_user_activity
from utils.limiters.login import LoginLimiter
from config import REDIS_URL

router = APIRouter(prefix="/auth", tags=["auth"])
bearer_scheme = HTTPBearer()
logger = logging.getLogger(__name__)

redis_client = Redis.from_url(REDIS_URL, decode_responses=True)
login_limiter = LoginLimiter(redis_client)


@router.post(
    "/login/",
    response_model=AuthResponseSerializer,
    status_code=status.HTTP_200_OK
)
async def login(
    data: LoginSerializer,
    t: dict = Depends(get_translation)
) -> AuthResponseSerializer:
    """
    Authenticate a user via email/password and issue JWT.
    """
    email = data.email.lower().strip()
    logger.info("Login attempt for email: %s", email)

    # 1) Rate-limit check
    if await login_limiter.is_blocked(email):
        logger.warning("Login blocked due to too many attempts: %s", email)
        raise HTTPException(status_code=429, detail=t["too_many_attempts"])

    # 2) Fetch user
    user = await UserService.get_by_email(email)
    if not user:
        logger.warning("Login failed, user not found: %s", email)
        await login_limiter.register_failed_attempt(email)
        raise HTTPException(status_code=400, detail=t["user_not_found"])

    # 3) Inactive user
    if not user.is_active:
        logger.warning("Login failed, inactive user: %s", email)
        raise HTTPException(status_code=403, detail=t["inactive_user"])

    # 4) Password verification
    if not user.check_password(data.password):
        logger.warning("Login failed, incorrect password: %s", email)
        await login_limiter.register_failed_attempt(email)
        raise HTTPException(status_code=400, detail=t["incorrect_password"])

    # 5) Email verified
    if not user.is_verified:
        logger.warning("Login failed, email not verified: %s", email)
        raise HTTPException(status_code=403, detail=t["email_not_verified"])

    # 6) Successful login — reset limiter counter
    await login_limiter.register_successful_login(email)

    # 7) Issue JWT
    token = create_access_token(subject=str(user.id), email=user.email)
    logger.info("User logged in successfully: %s", email)

    # 8) Log activity
    log_user_activity.delay(user.id, "login")

    return AuthResponseSerializer(token=token, auth_type="Bearer")


@router.post(
    "/login/oauth2/",
    response_model=AuthResponseSerializer,
    status_code=status.HTTP_200_OK
)
async def oauth2_login(
    data: OAuth2SignInSerializer,
    t: dict = Depends(get_translation)
) -> AuthResponseSerializer:
    """
    Authenticate a user via OAuth2 (Google or Apple) and issue JWT.
    """
    logger.info("OAuth2 login attempt type=%s", data.auth_type)

    result = await oauth2_sign_in(
        token=data.token,
        auth_type=data.auth_type,
        client_id=data.client_id
    )
    access_token = result["access_token"]

    payload = decode_access_token(access_token)
    user_id = int(payload["sub"])

    logger.info("OAuth2 login successful for user_id=%s", user_id)
    log_user_activity.delay(user_id, f"oauth2_{data.auth_type}")

    return AuthResponseSerializer(token=access_token, auth_type="Bearer")
