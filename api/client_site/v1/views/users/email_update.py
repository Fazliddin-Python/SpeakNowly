import logging

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBearer
from redis.asyncio import Redis

from ...serializers.users.email_update import EmailUpdateSerializer, CheckOTPEmailSerializer
from services.users.verification_service import VerificationService
from services.users.user_service import UserService
from utils.auth.auth import get_current_user
from utils.i18n import get_translation
from tasks.users.activity_tasks import log_user_activity
from models.users.verification_codes import VerificationType
from utils.limiters.email_update import EmailUpdateLimiter
from config import REDIS_URL

router = APIRouter()
bearer = HTTPBearer()
logger = logging.getLogger(__name__)

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
    logger.info("Email-update requested for user %s -> %s", user_id, new_email)

    # 3. Prevent duplicate email
    existing = await UserService.get_by_email(new_email)
    if existing and existing.id != user_id:
        logger.warning("Email-update failed: %s already in use", new_email)
        raise HTTPException(status_code=400, detail=t["user_already_registered"])

    # 4. Rate-limit check
    if await email_update_limiter.is_blocked(new_email):
        logger.warning("Email-update blocked due to too many attempts: %s", new_email)
        raise HTTPException(status_code=429, detail=t["too_many_attempts"])

    # 5. Register attempt for limiter
    await email_update_limiter.register_failed_attempt(new_email)

    # 6. Send OTP
    try:
        await VerificationService.send_verification_code(
            email=new_email,
            verification_type=VerificationType.UPDATE_EMAIL
        )
    except HTTPException as exc:
        detail = exc.detail if isinstance(exc.detail, str) else t["otp_resend_failed"]
        logger.warning("Email-update OTP failed: %s", detail)
        raise HTTPException(status_code=exc.status_code, detail=detail)

    # 7. Log activity
    log_user_activity.delay(user_id, "email_update_request")

    # 8. Return response
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
    logger.info("Confirm-email-update for user %s: new=%s code=%s", user_id, new_email, data.code)

    # 1. Prevent duplicate email
    existing = await UserService.get_by_email(new_email)
    if existing and existing.id != user_id:
        logger.warning("Confirm-email-update failed: %s already in use", new_email)
        raise HTTPException(status_code=400, detail=t["user_already_registered"])

    # 2. Verify code
    try:
        await VerificationService.verify_code(
            email=new_email,
            code=str(data.code),
            verification_type=VerificationType.UPDATE_EMAIL
        )
    except HTTPException as exc:
        detail = exc.detail if isinstance(exc.detail, str) else t["otp_verification_failed"]
        logger.warning("Confirm-email-update failed: %s", detail)
        raise HTTPException(status_code=exc.status_code, detail=detail)

    # 3. Reset limiter
    await email_update_limiter.reset(new_email)

    # 4. Update email
    await UserService.update_user(user_id, email=new_email)

    # 5. Delete unused codes
    await VerificationService.delete_unused_codes(
        email=new_email,
        verification_type=VerificationType.UPDATE_EMAIL
    )

    # 6. Log activity
    log_user_activity.delay(user_id, "email_update_confirm")

    # 7. Return response
    return {"message": t["code_confirmed"]}
