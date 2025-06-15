from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBearer
from datetime import datetime
from redis.asyncio import Redis

from ...serializers.users import LoginSerializer, OAuth2SignInSerializer, AuthResponseSerializer
from services.users import UserService
from tasks.users import log_user_activity
from utils.limiters import get_login_limiter
from utils.auth.oauth2_auth import oauth2_sign_in
from utils.auth import create_access_token, create_refresh_token, decode_access_token
from utils.i18n import get_translation
from config import REDIS_URL

router = APIRouter()
bearer_scheme = HTTPBearer()

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

    try:
        if await login_limiter.is_blocked(email):
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=t["too_many_attempts"].format(minutes=15))

        user = await UserService.authenticate(email, data.password, t)
        await login_limiter.reset(email)
        await UserService.update_user(user.id, t, last_login=datetime.utcnow())
        access_token = await create_access_token(subject=str(user.id), email=user.email)
        refresh_token = await create_refresh_token(subject=str(user.id), email=user.email)
        await log_user_activity.delay(user.id, "login")
        return AuthResponseSerializer(access_token=access_token, refresh_token=refresh_token, auth_type="Bearer")

    except HTTPException as exc:
        await login_limiter.register_attempt(email)
        detail = exc.detail if isinstance(exc.detail, str) else t.get("internal_error", "Internal server error")
        raise HTTPException(status_code=exc.status_code, detail=detail)
    except Exception:
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
    try:
        result = await oauth2_sign_in(
            token=data.token,
            auth_type=data.auth_type,
            client_id=data.client_id
        )
        access_token = result.get("access_token")
        refresh_token = result.get("refresh_token")
        if not access_token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=t.get("invalid_oauth2_token", "Invalid OAuth2 token"))

        payload = await decode_access_token(access_token)
        user_id = int(payload["sub"])

        user = await UserService.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=t.get("user_not_found", "User not found"))
        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=t.get("inactive_user", "User is inactive"))

        await UserService.update_user(user.id, t, last_login=datetime.utcnow())
        await log_user_activity.delay(user_id, f"oauth2_{data.auth_type}")

        return AuthResponseSerializer(access_token=access_token, refresh_token=refresh_token, auth_type="Bearer")

    except HTTPException as exc:
        detail = exc.detail if isinstance(exc.detail, str) else t.get("internal_error", "Internal server error")
        raise HTTPException(status_code=exc.status_code, detail=detail)
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=t.get("internal_error", "Internal server error"))