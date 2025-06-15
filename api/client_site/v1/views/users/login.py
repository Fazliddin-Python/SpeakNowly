from datetime import datetime
import logging
import asyncio
import traceback

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBearer
from redis.asyncio import Redis

from ...serializers.users.login import LoginSerializer, OAuth2SignInSerializer, AuthResponseSerializer
from services.users.user_service import UserService
from utils.auth.auth import create_access_token, create_refresh_token, decode_access_token
from utils.auth.oauth2_auth import oauth2_sign_in
from utils.i18n import get_translation
from tasks.users import log_user_activity
from utils.limiters import get_login_limiter
from config import REDIS_URL

router = APIRouter()
bearer_scheme = HTTPBearer()
logger = logging.getLogger(__name__)

redis_client = Redis.from_url(REDIS_URL, decode_responses=True)
login_limiter = get_login_limiter(redis_client)


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
    Authenticate a user via email and password, then issue JWT.

    Steps:
    1. Normalize and validate the email.
    2. Check login rate limiting.
    3. Authenticate the user via the service (checks email, password, status, verification).
    4. Reset limiter counter on successful login.
    5. Update the user's last_login timestamp.
    6. Generate JWT tokens (access and refresh).
    7. Log the successful login and user activity.
    8. Return the response with both tokens.
    """
    email = data.email.lower().strip()
    logger.info("Login attempt for email: %s", email)

    try:
        # 1. Check login rate limiting
        if await login_limiter.is_blocked(email):
            logger.warning("Login blocked due to too many attempts: %s", email)
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=t["too_many_attempts"])

        # 2. Authenticate user via service (all checks inside)
        user = await UserService.authenticate(email, data.password, t)

        # 3. Reset limiter counter on success
        await login_limiter.reset(email)

        # 4. Update last_login timestamp
        await UserService.update_user(user.id, t, last_login=datetime.utcnow())

        # 5. Generate JWT tokens
        access_token = create_access_token(subject=str(user.id), email=user.email)
        refresh_token = create_refresh_token(subject=str(user.id), email=user.email)
        logger.info("User logged in successfully: %s", email)

        # 6. Log user activity
        log_user_activity.delay(user.id, "login")

        # 7. Return response with tokens
        return AuthResponseSerializer(access_token=access_token, refresh_token=refresh_token, auth_type="Bearer")

    except HTTPException as exc:
        logger.warning("HTTPException during login: %s\n%s", exc.detail, traceback.format_exc())
        await login_limiter.register_attempt(email)
        detail = exc.detail if isinstance(exc.detail, str) else t.get("internal_error", "Internal server error")
        raise HTTPException(status_code=exc.status_code, detail=detail)
    except Exception as exc:
        logger.error("Unexpected error during login: %s\n%s", exc, traceback.format_exc())
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=t.get("internal_error", "Internal server error"))


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
    5. Update last_login and log activity.
    6. Return response with both tokens.
    """
    logger.info("OAuth2 login attempt type=%s", data.auth_type)
    try:
        result = await oauth2_sign_in(
            token=data.token,
            auth_type=data.auth_type,
            client_id=data.client_id
        )
        access_token = result.get("access_token")
        refresh_token = result.get("refresh_token")
        if not access_token:
            logger.warning("OAuth2 login failed: no access_token in result")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=t.get("invalid_oauth2_token", "Invalid OAuth2 token"))

        payload = decode_access_token(access_token)
        user_id = int(payload["sub"])

        user = await UserService.get_by_id(user_id)
        if not user:
            logger.warning("OAuth2 login failed: user not found (id=%s)", user_id)
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=t.get("user_not_found", "User not found"))
        if not user.is_active:
            logger.warning("OAuth2 login failed: inactive user (id=%s)", user_id)
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=t.get("inactive_user", "User is inactive"))

        await UserService.update_user(user.id, t, last_login=datetime.utcnow())
        log_user_activity.delay(user_id, f"oauth2_{data.auth_type}")
        logger.info("OAuth2 login successful for user_id=%s", user_id)

        return AuthResponseSerializer(access_token=access_token, refresh_token=refresh_token, auth_type="Bearer")

    except HTTPException as exc:
        logger.warning("HTTPException during OAuth2 login: %s\n%s", exc.detail, traceback.format_exc())
        detail = exc.detail if isinstance(exc.detail, str) else t.get("internal_error", "Internal server error")
        raise HTTPException(status_code=exc.status_code, detail=detail)
    except Exception as exc:
        logger.error("Unexpected error during OAuth2 login: %s\n%s", exc, traceback.format_exc())
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=t.get("internal_error", "Internal server error"))
