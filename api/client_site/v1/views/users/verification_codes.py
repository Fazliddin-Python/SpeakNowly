import logging

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBearer
from typing import Dict

from ...serializers.users.verification_codes import (
    CheckOTPSerializer,
    CheckOTPResponseSerializer,
)
from services.users.verification_service import VerificationService
from services.users.user_service import UserService
from utils.auth.auth import create_access_token, create_refresh_token
from utils.i18n import get_translation
from tasks.users import log_user_activity
from models.users.verification_codes import VerificationType

router = APIRouter()
security = HTTPBearer()
logger = logging.getLogger(__name__)


@router.post(
    "/verify-otp",
    response_model=CheckOTPResponseSerializer,
    status_code=status.HTTP_200_OK
)
async def verify_otp(
    data: CheckOTPSerializer,
    t: Dict[str, str] = Depends(get_translation),
) -> CheckOTPResponseSerializer:
    """
    Verify a one-time password (OTP) and return JWT tokens upon success.

    Steps:
    1. Validate input via serializer (email, code, verification_type).
    2. Call VerificationService.verify_code() to confirm OTP.
    3. If verification_type == REGISTER, mark the user as verified.
    4. Generate both access and refresh tokens.
    5. Delete any unused codes of this type for the email.
    6. Log the verification action asynchronously.
    7. Return a success message along with access_token and refresh_token.
    """
    logger.info("Attempting OTP verification for %s [%s]", data.email, data.verification_type)

    # 2. Verify the OTP; this raises HTTPException if invalid or expired
    try:
        user = await VerificationService.verify_code(
            email=data.email,
            code=str(data.code),
            verification_type=data.verification_type
        )
    except HTTPException as exc:
        # Use translation if available, else fallback to a default string
        error_detail = exc.detail if isinstance(exc.detail, str) else t.get("otp_verification_failed", "Verification failed.")
        logger.warning("OTP verification failed for %s: %s", data.email, error_detail)
        raise HTTPException(status_code=exc.status_code, detail=error_detail)

    # 3. If this is a registration flow, mark user.is_verified = True
    if data.verification_type == VerificationType.REGISTER:
        await UserService.update_user(user.id, t, is_verified=True)
        logger.info("User %s (ID: %s) marked as verified", user.email, user.id)

    # 4. Generate access and refresh tokens now that the user is verified
    access_token = create_access_token(subject=str(user.id), email=user.email)
    refresh_token = create_refresh_token(subject=str(user.id), email=user.email)
    logger.info("Generated access and refresh tokens for %s", user.email)

    # 5. Clean up any remaining unused codes for this email/type
    await VerificationService.delete_unused_codes(
        email=data.email,
        verification_type=data.verification_type
    )
    logger.debug("Deleted unused OTPs for %s [%s]", data.email, data.verification_type)

    # 6. Log the verification action asynchronously
    log_user_activity.delay(user.id, f"verify_{data.verification_type}")
    logger.debug("Logged activity: verify_%s for user ID %s", data.verification_type, user.id)

    # 7. Return message + both tokens
    return CheckOTPResponseSerializer(
        message=t.get("code_confirmed", "Verification successful."),
        access_token=access_token,
        refresh_token=refresh_token
    )
