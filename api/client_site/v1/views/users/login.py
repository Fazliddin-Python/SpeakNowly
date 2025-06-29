from fastapi import APIRouter, HTTPException, Query, status, Depends
from starlette.responses import RedirectResponse
from fastapi.security import HTTPBearer
from datetime import datetime
from urllib.parse import unquote
from redis.asyncio import Redis
import hashlib
import hmac


from ...serializers.users import (
    LoginSerializer, OAuth2SignInSerializer, AuthResponseSerializer, StartTelegramAuthSerializer, TelegramAuthSerializer
)
from services.users import UserService, EmailService
from models.users import User
from utils.arq_pool import get_arq_redis
from utils.limiters import get_login_limiter
from utils.auth.oauth2_auth import oauth2_sign_in
from utils.auth.tg_auth import telegram_sign_in
from utils.auth import create_access_token, create_refresh_token, decode_access_token, get_current_user
from utils.i18n import get_translation
from config import REDIS_URL, TELEGRAM_BOT_TOKEN

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


def verify_telegram_hash(data: dict) -> bool:
    """
    Verify HMAC-SHA256 signature sent by Telegram Login Widget.
    """
    secret_key = hashlib.sha256(TELEGRAM_BOT_TOKEN.encode()).digest()
    payload = {k: v for k, v in data.items() if k != "hash"}
    check_string = "\n".join(f"{k}={v}" for k, v in sorted(payload.items()))
    computed = hmac.new(secret_key, check_string.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(computed, data["hash"])


@router.get(
    "/login/telegram/",
    response_class=RedirectResponse,
    status_code=status.HTTP_302_FOUND
)
async def login_via_telegram(
    data: TelegramAuthSerializer = Depends(),
    redis: Redis = Depends(get_arq_redis),
    t: dict = Depends(get_translation),
):
    """
    1. Verify Telegram's HMAC signature.
    2. Decode percent‑encoded photo_url.
    3. Find or create User by telegram_id.
    4. Send welcome email if newly registered.
    5. Update last_login via UserService.
    6. Issue JWT tokens.
    7. Enqueue activity log.
    8. Redirect to frontend with tokens.
    """
    raw = data.dict()

    # 1. Verify signature
    if not verify_telegram_hash(raw):
        raise HTTPException(status_code=400, detail="Invalid Telegram data signature")

    tg_id = str(raw["id"])

    # 2. Decode photo_url if present
    decoded_photo = unquote(raw["photo_url"]) if raw.get("photo_url") else None

    # 3. Lookup or create user
    user = await User.get_or_none(telegram_id=tg_id)
    newly_created = False
    if not user:
        default_email = f"{tg_id}@speaknowly.com"
        # create user with empty (random) password
        import secrets
        random_pw = secrets.token_urlsafe(32)
        user = User(
            email=default_email,
            first_name=raw["first_name"],
            last_name=raw.get("last_name"),
            photo=decoded_photo,
            telegram_id=tg_id,
            is_verified=True,
            is_active=True,
        )
        user.set_password(random_pw)
        await user.save()
        newly_created = True

    # 4. Вместо email — создать одно Message на трёх языках в одном сообщении
    if newly_created:
        from models.notifications import Message, MessageType

        # Титул на трёх языках
        title = "Salom | Привет | Welcome"

        # Короткое описание на трёх языках
        description = (
            "🎁 Telegram bonuslar! | 🎁 Получай бонусы в Telegram! | 🎁 Get bonuses in Telegram!"
        )

        # Контент на трёх языках (HTML)
        content = """
<div>
  <p>🇺🇿 <b>Kanalimizga obuna bo‘ling va promokodlar, IELTS materiallar va yangiliklarni birinchi bo‘lib oling!</b></p>
  <p>🇷🇺 <b>Подпишись на канал и получай промокоды, материалы по IELTS и новости первым!</b></p>
  <p>🇬🇧 <b>Subscribe to our channel for promo codes, IELTS tips, and updates first!</b></p>
  <p style="margin-top:16px;">
    <a href="https://t.me/SpeakNowly" target="_blank" style="color:#4F6AFC;font-weight:bold;text-decoration:none;">
      t.me/SpeakNowly
    </a>
  </p>
</div>
"""

        await Message.create(
            user=user,
            type=MessageType.SITE,
            title=title,
            description=description,
            content=content,
        )
    # 5. Update last_login
    await UserService.update_user(user.id, t, last_login=datetime.utcnow())

    # 6. Generate JWT
    access_token = await create_access_token(subject=str(user.id), email=user.email)
    refresh_token = await create_refresh_token(subject=str(user.id), email=user.email)

    # 7. Log activity
    await redis.enqueue_job(
        "log_user_activity", user_id=user.id, action="telegram_login"
    )

    # 8. Redirect with tokens
    frontend_url = "https://speaknowly.com/auth"
    qs = (
        f"?access_token={access_token}"
        f"&refresh_token={refresh_token}"
        f"&telegrampermission=true"
    )
    return RedirectResponse(frontend_url + qs)