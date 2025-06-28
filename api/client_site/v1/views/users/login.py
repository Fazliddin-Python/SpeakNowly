from fastapi import APIRouter, HTTPException, Query, status, Depends
from starlette.responses import RedirectResponse
from fastapi.security import HTTPBearer
from datetime import datetime
from redis.asyncio import Redis

from ...serializers.users import (
    LoginSerializer, OAuth2SignInSerializer, AuthResponseSerializer, StartTelegramAuthSerializer, TelegramAuthSerializer
)
from services.users import UserService
from utils.limiters import get_login_limiter
from utils.auth.oauth2_auth import oauth2_sign_in
from utils.telegram_bot import send_confirmation_message
from utils.auth.tg_auth import telegram_sign_in
from utils.auth import create_access_token, create_refresh_token, decode_access_token, get_current_user
from utils.i18n import get_translation
from utils.arq_pool import get_arq_redis
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
    t: dict = Depends(get_translation),
    redis=Depends(get_arq_redis)
) -> AuthResponseSerializer:
    """
    Authenticate user and issue JWT tokens:
    - Rate limit login attempts
    - Validate credentials
    - Update last login
    - Enqueue activity log
    """
    email = data.email.lower().strip()

    # Rate limit check
    if await login_limiter.is_blocked(email):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=t["too_many_attempts"]
        )

    try:
        user = await UserService.authenticate(email, data.password, t)
        await login_limiter.reset(email)
        await UserService.update_user(user.id, t, last_login=datetime.utcnow())

        # Generate tokens
        access_token = await create_access_token(subject=str(user.id), email=user.email)
        refresh_token = await create_refresh_token(subject=str(user.id), email=user.email)

        # Enqueue activity log job
        await redis.enqueue_job(
            "log_user_activity", user_id=user.id, action="login"
        )

        return AuthResponseSerializer(
            access_token=access_token,
            refresh_token=refresh_token,
            auth_type="Bearer"
        )

    except HTTPException as exc:
        # Register failed attempt
        await login_limiter.register_attempt(email)
        raise


@router.post(
    "/login/oauth2/",
    response_model=AuthResponseSerializer,
    status_code=status.HTTP_200_OK
)
async def oauth2_login(
    data: OAuth2SignInSerializer,
    t: dict = Depends(get_translation),
    redis=Depends(get_arq_redis)
) -> AuthResponseSerializer:
    """
    Authenticate via OAuth2 and issue JWT tokens:
    - Validate OAuth2 token
    - Decode user
    - Update last login
    - Enqueue activity log
    """
    result = await oauth2_sign_in(
        token=data.token,
        auth_type=data.auth_type,
        client_id=data.client_id
    )
    access_token = result["access_token"]
    refresh_token = result["refresh_token"]

    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=t.get("invalid_oauth2_token", "Invalid OAuth2 token")
        )

    payload = await decode_access_token(access_token)
    user_id = int(payload["sub"])
    user = await UserService.get_by_id(user_id)

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=t.get("user_not_found", "User not found")
        )

    await UserService.update_user(user.id, t, last_login=datetime.utcnow())

    # Enqueue activity log job
    await redis.enqueue_job(
        "log_user_activity", user_id=user.id, action=f"oauth2_{data.auth_type}"
    )

    return AuthResponseSerializer(
        access_token=access_token,
        refresh_token=refresh_token,
        auth_type="Bearer"
    )


@router.post(
    "/login/telegram-start/",
    status_code=status.HTTP_200_OK
)
async def start_telegram_auth(
    data: StartTelegramAuthSerializer,
    t: dict = Depends(get_translation),
):
    """
    Step 1: User enters phone → send Telegram confirmation message with button.
    """
    await send_confirmation_message(data.telegram_id, data.phone, data.lang)

    return {"detail": t.get("telegram_verification_started", "Verification started")}


@router.get(
    "/login/telegram/",
    response_class=RedirectResponse,
    status_code=status.HTTP_302_FOUND
)
async def login_via_telegram(
    data: TelegramAuthSerializer,
    redis=Depends(get_arq_redis),
    t: dict = Depends(get_translation),
):
    """
    Step 2: User clicks 'Confirm' in Telegram → 
    FastAPI validates, links user, issues JWT and redirects to front.
    """
    tokens = await telegram_sign_in(
        telegram_data=data.dict(include={
            "id", "first_name", "last_name", "username",
            "photo_url", "auth_date", "hash"
        }),
        email=None,
        phone=data.phone
    )

    await redis.enqueue_job(
        "log_user_activity",
        user_id=int(tokens["access_token"].split(".")[0]),
        action="telegram_login"
    )

    frontend_url = "https://speaknowly.com/auth"
    redirect_qs = (
        f"?access_token={tokens['access_token']}"
        f"&refresh_token={tokens['refresh_token']}"
        f"&telegrampermission=true"
    )
    
    return RedirectResponse(frontend_url + redirect_qs)