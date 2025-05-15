import logging
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBearer
from typing import Dict

from ...serializers.users.verification_codes import (
    CheckOTPSerializer,
    CheckOTPResponseSerializer,
    ResendOTPSchema,
    ResendOTPResponseSerializer
)
from services.users.verification_service import VerificationService
from services.users.user_service import UserService
from utils.auth.auth import create_access_token
from utils.i18n import get_translation
from tasks.users.activity_tasks import log_user_activity
from models.users.verification_codes import VerificationType

router = APIRouter(prefix="/auth", tags=["verification"])
bearer = HTTPBearer()
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
    """Verify OTP and issue access token."""
    logger.info("Verifying OTP for %s type=%s", data.email, data.verification_type)

    try:
        user = await VerificationService.verify_code(
            email=data.email,
            code=data.code,
            verification_type=data.verification_type
        )
    except HTTPException as exc:
        detail = exc.detail if isinstance(exc.detail, str) else t["otp_verification_failed"]
        logger.warning("OTP verification failed: %s", detail)
        raise HTTPException(status_code=exc.status_code, detail=detail)

    if data.verification_type == VerificationType.REGISTER:
        await UserService.update_user(user.id, is_verified=True)
        logger.info("User %s marked as verified", user.email)

    token = create_access_token(subject=str(user.id), email=user.email)
    logger.info("OTP verified, token issued for %s", user.email)

    await VerificationService.delete_unused_codes(
        email=data.email,
        verification_type=data.verification_type
    )

    log_user_activity.delay(user.id, f"verify_{data.verification_type}")

    return CheckOTPResponseSerializer(
        message=t["code_confirmed"],
        access_token=token
    )


@router.post(
    "/resend-otp",
    response_model=ResendOTPResponseSerializer,
    status_code=status.HTTP_202_ACCEPTED
)
async def resend_otp(
    data: ResendOTPSchema,
    t: Dict[str, str] = Depends(get_translation)
) -> ResendOTPResponseSerializer:
    """Resend an OTP code to user email."""
    logger.info("Resend OTP requested for %s type=%s", data.email, data.verification_type)

    try:
        await VerificationService.send_verification_code(
            email=data.email,
            verification_type=data.verification_type
        )
    except HTTPException as exc:
        detail = exc.detail if isinstance(exc.detail, str) else t["otp_resend_failed"]
        logger.warning("Resend OTP failed: %s", detail)
        raise HTTPException(status_code=exc.status_code, detail=detail)

    logger.info("OTP resent to %s", data.email)
    return ResendOTPResponseSerializer(message=t["code_resent"])
