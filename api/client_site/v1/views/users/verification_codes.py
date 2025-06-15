from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBearer
from typing import Dict

from ...serializers.users import CheckOTPSerializer, CheckOTPResponseSerializer
from services.users import VerificationService, UserService
from tasks.users import log_user_activity
from models.users import VerificationType
from utils.auth import create_access_token, create_refresh_token
from utils.i18n import get_translation

router = APIRouter()
security = HTTPBearer()

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
    try:
        user = await VerificationService.verify_code(
            email=data.email,
            code=str(data.code),
            verification_type=data.verification_type
        )
    except HTTPException as exc:
        error_detail = exc.detail if isinstance(exc.detail, str) else t.get("otp_verification_failed", "Verification failed.")
        raise HTTPException(status_code=exc.status_code, detail=error_detail)

    if data.verification_type == VerificationType.REGISTER:
        await UserService.update_user(user.id, t, is_verified=True)

    access_token = await create_access_token(subject=str(user.id), email=user.email)
    refresh_token = await create_refresh_token(subject=str(user.id), email=user.email)

    await VerificationService.delete_unused_codes(
        email=data.email,
        verification_type=data.verification_type
    )

    await log_user_activity.delay(user.id, f"verify_{data.verification_type}")

    return CheckOTPResponseSerializer(
        message=t.get("code_confirmed", "Verification successful."),
        access_token=access_token,
        refresh_token=refresh_token
    )
