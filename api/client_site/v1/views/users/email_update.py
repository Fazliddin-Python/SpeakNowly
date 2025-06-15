from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBearer
from redis.asyncio import Redis

from ...serializers.users import EmailUpdateSerializer, CheckOTPEmailSerializer
from services.users import VerificationService, UserService
from tasks.users import log_user_activity
from models.users import VerificationType
from utils.limiters import EmailUpdateLimiter
from utils.auth import get_current_user
from utils.i18n import get_translation
from config import REDIS_URL

router = APIRouter()
bearer = HTTPBearer()

redis_client = Redis.from_url(REDIS_URL, decode_responses=True)
email_update_limiter = EmailUpdateLimiter(redis_client)

@router.post(
    "/email-update/",
    status_code=status.HTTP_200_OK
)
async def request_email_update(
    data: EmailUpdateSerializer,
    current=Depends(get_current_user),
    t: dict = Depends(get_translation)
):
    """
    Request to update the user's email address.

    Steps:
    1. Authenticate user.
    2. Normalize and validate new email.
    3. Check if email is already in use.
    4. Rate-limit check.
    5. Register attempt for limiter.
    6. Send verification code.
    7. Log activity.
    8. Return response.
    """
    user_id = current.id
    new_email = data.email.lower().strip()

    existing = await UserService.get_by_email(new_email)
    if existing and existing.id != user_id:
        raise HTTPException(status_code=400, detail=t["user_already_registered"])

    if await email_update_limiter.is_blocked(new_email):
        raise HTTPException(status_code=429, detail=t["too_many_attempts"].format(minutes=15))

    await email_update_limiter.register_attempt(new_email)

    try:
        await VerificationService.send_verification_code(
            email=new_email,
            verification_type=VerificationType.UPDATE_EMAIL
        )
    except HTTPException as exc:
        detail = exc.detail if isinstance(exc.detail, str) else t["otp_resend_failed"]
        raise HTTPException(status_code=exc.status_code, detail=detail)

    await log_user_activity.delay(user_id, "email_update_request")

    return {"message": t["verification_sent"]}


@router.post(
    "/email-update/confirm/",
    status_code=status.HTTP_200_OK
)
async def confirm_email_update(
    data: CheckOTPEmailSerializer,
    current=Depends(get_current_user),
    t: dict = Depends(get_translation)
):
    """
    Confirm email update with OTP.

    Steps:
    1. Authenticate user.
    2. Normalize and validate new email.
    3. Prevent duplicate email.
    4. Verify OTP code.
    5. Reset limiter.
    6. Update user's email.
    7. Delete unused codes.
    8. Log activity.
    9. Return response.
    """
    user_id = current.id
    new_email = data.new_email.lower().strip()

    existing = await UserService.get_by_email(new_email)
    if existing and existing.id != user_id:
        raise HTTPException(status_code=400, detail=t["user_already_registered"])

    try:
        await VerificationService.verify_code(
            email=new_email,
            code=str(data.code),
            verification_type=VerificationType.UPDATE_EMAIL,
            user_id=user_id
        )
    except HTTPException as exc:
        detail = exc.detail if isinstance(exc.detail, str) else t["otp_verification_failed"]
        raise HTTPException(status_code=exc.status_code, detail=detail)

    await email_update_limiter.reset_attempts(new_email)
    user = await UserService.update_user(user_id, t, email=new_email)
    await VerificationService.delete_unused_codes(
        email=new_email,
        verification_type=VerificationType.UPDATE_EMAIL
    )
    await log_user_activity.delay(user_id, "email_update_confirm")

    return {"message": t["code_confirmed"]}
