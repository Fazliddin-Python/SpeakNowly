from fastapi import APIRouter, HTTPException, status
from ...serializers.users.email_update import EmailUpdateSerializer, CheckOTPEmailSerializer
from models.users.verification_codes import VerificationCode
from models.users.users import User

router = APIRouter()


@router.post("/email-update/", status_code=status.HTTP_200_OK)
async def email_update(data: EmailUpdateSerializer):
    """
    Sends OTP for updating email.
    """
    # Check if a user with the given email exists
    user = await User.filter(email=data.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User with this email not found")

    # Generate and save OTP
    otp_code = VerificationCode.generate_otp()  # Method to generate OTP
    await VerificationCode.create(
        email=data.email,
        user_id=user.id,
        verification_type=VerificationCode.UPDATE_EMAIL,
        code=otp_code,
        is_used=False,
        is_expired=False
    )

    # Logic for sending OTP (e.g., via email)
    # send_email_otp(data.email, otp_code)  # Example function call for sending OTP

    return {"message": "OTP for updating email has been successfully sent"}


@router.post("/email-update/check-otp/", status_code=status.HTTP_200_OK)
async def check_email_otp(data: CheckOTPEmailSerializer):
    """
    Verifies OTP for updating email.
    """
    # Check if a record with the given email and code exists
    verification_code = await VerificationCode.filter(
        email=data.email,
        code=data.code,
        is_used=False,
        is_expired=False
    ).first()

    if not verification_code:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")

    # Mark the code as used
    verification_code.is_used = True
    await verification_code.save()

    return {"message": "OTP has been successfully verified"}