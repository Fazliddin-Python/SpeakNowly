from datetime import datetime
import logging
import asyncio
import traceback

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

router = APIRouter()
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

    Steps:
    1. Normalize and validate email.
    2. Check login rate limit.
    3. Fetch user by email.
    4. Check if user is active.
    5. Verify password.
    6. Check if email is verified.
    7. Reset limiter on success.
    8. Issue JWT and log activity.
    9. Return response.
    """
    email = data.email.lower().strip()
    logger.info("Login attempt for email: %s", email)

    try:
        # 1. Rate-limit check
        if await login_limiter.is_blocked(email):
            logger.warning("Login blocked due to too many attempts: %s", email)
            raise HTTPException(status_code=429, detail=t["too_many_attempts"])

        # 2. Fetch user
        user = await UserService.get_by_email(email)
        if not user:
            logger.warning("Login failed, user not found: %s", email)
            await login_limiter.register_failed_attempt(email)
            raise HTTPException(status_code=401, detail=t["invalid_credentials"])

        # 3. Check if user is active
        if not user.is_active:
            logger.warning("Login failed, inactive user: %s", email)
            raise HTTPException(status_code=403, detail=t["inactive_user"])

        # 4. Password verification (run in thread pool if bcrypt is sync)
        loop = asyncio.get_event_loop()
        password_valid = await loop.run_in_executor(None, user.check_password, data.password)
        if not password_valid:
            logger.warning("Login failed, incorrect password: %s", email)
            await login_limiter.register_failed_attempt(email)
            raise HTTPException(status_code=401, detail=t["invalid_credentials"])

        # 5. Email verified
        if not user.is_verified:
            logger.warning("Login failed, email not verified: %s", email)
            raise HTTPException(status_code=403, detail=t["email_not_verified"])

        # 6. Successful login — reset limiter counter
        await login_limiter.reset_attempts(email)

        # 6.1. Update last_login
        await UserService.update_user(user.id, last_login=datetime.utcnow())

        # 7. Issue JWT
        token = create_access_token(subject=str(user.id), email=user.email)
        logger.info("User logged in successfully: %s", email)

        # 8. Log activity
        log_user_activity.delay(user.id, "login")

        return AuthResponseSerializer(token=token, auth_type="Bearer")

    except HTTPException as exc:
        logger.warning("HTTPException during login: %s\n%s", exc.detail, traceback.format_exc())
        detail = exc.detail if isinstance(exc.detail, str) else t.get("internal_error", "Internal server error")
        raise HTTPException(status_code=exc.status_code, detail=detail)
    except Exception as exc:
        logger.error("Unexpected error during login: %s\n%s", exc, traceback.format_exc())
        raise HTTPException(status_code=500, detail=t.get("internal_error", "Internal server error"))


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

    Steps:
    1. Validate OAuth2 input.
    2. Authenticate via oauth2_sign_in utility.
    3. Decode JWT and extract user ID.
    4. Check user status.
    5. Log activity.
    6. Return response.
    """
    logger.info("OAuth2 login attempt type=%s", data.auth_type)
    try:
        result = await oauth2_sign_in(
            token=data.token,
            auth_type=data.auth_type,
            client_id=data.client_id
        )
        access_token = result.get("access_token")
        if not access_token:
            logger.warning("OAuth2 login failed: no access_token in result")
            raise HTTPException(status_code=401, detail=t.get("invalid_oauth2_token", "Invalid OAuth2 token"))

        payload = decode_access_token(access_token)
        user_id = int(payload["sub"])

        user = await UserService.get_by_id(user_id)
        if not user:
            logger.warning("OAuth2 login failed: user not found (id=%s)", user_id)
            raise HTTPException(status_code=404, detail=t.get("user_not_found", "User not found"))
        if not user.is_active:
            logger.warning("OAuth2 login failed: inactive user (id=%s)", user_id)
            raise HTTPException(status_code=403, detail=t.get("inactive_user", "User is inactive"))

        logger.info("OAuth2 login successful for user_id=%s", user_id)
        await UserService.update_user(user.id, last_login=datetime.utcnow())
        log_user_activity.delay(user_id, f"oauth2_{data.auth_type}")

        return AuthResponseSerializer(token=access_token, auth_type="Bearer")

    except HTTPException as exc:
        logger.warning("HTTPException during OAuth2 login: %s\n%s", exc.detail, traceback.format_exc())
        detail = exc.detail if isinstance(exc.detail, str) else t.get("internal_error", "Internal server error")
        raise HTTPException(status_code=exc.status_code, detail=detail)
    except Exception as exc:
        logger.error("Unexpected error during OAuth2 login: %s\n%s", exc, traceback.format_exc())
        raise HTTPException(status_code=500, detail=t.get("internal_error", "Internal server error"))
