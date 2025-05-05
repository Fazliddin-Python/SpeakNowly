from fastapi import APIRouter, HTTPException, status
from ..serializers.email_update import EmailUpdateSerializer, CheckOTPEmailSerializer

router = APIRouter()


@router.post("/email-update/", status_code=status.HTTP_200_OK)
async def email_update(data: EmailUpdateSerializer):
    """
    Send an email update OTP.
    """
    # Example logic for sending OTP
    if not await User.filter(email=data.email).exists():
        raise HTTPException(status_code=404, detail="User with this email does not exist")
    # Simulate sending OTP
    return {"message": "Email update OTP sent successfully"}


@router.post("/email-update/check-otp/", status_code=status.HTTP_200_OK)
async def check_email_otp(data: CheckOTPEmailSerializer):
    """
    Verify the OTP for email update.
    """
    # Example logic for OTP verification
    if not await VerificationCode.filter(email=data.email, code=data.code, is_used=False).exists():
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")
    return {"message": "OTP verified successfully"}