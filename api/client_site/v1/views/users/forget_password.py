from fastapi import APIRouter, HTTPException, status
from models.users.users import User
from utils.auth import create_access_token
from ...serializers.users.forget_password import ForgetPasswordSerializer, SetNewPasswordSerializer
from services.users.user_service import UserService

router = APIRouter()


@router.post("/forget-password/", status_code=status.HTTP_200_OK)
async def forget_password(data: ForgetPasswordSerializer):
    """
    Handle the password reset request.
    """
    user = await UserService.get_user_by_email(data.email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Generate a confirmation code (e.g., a 5-digit code)
    code = 12345  # Here you can use a code generator
    # Save the code in the database or send it via email
    # For example, VerificationCode.update_or_create(...)

    return {"message": "Verification code sent to your email"}


@router.post("/set-new-password/", status_code=status.HTTP_200_OK)
async def set_new_password(data: SetNewPasswordSerializer):
    """
    Set a new password.
    """
    # Verify the confirmation code
    # For example, VerificationCode.objects.filter(...).exists()

    user = await UserService.get_user_by_email(data.email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Set the new password
    user.set_password(data.password)
    await user.save()

    return {"message": "Password updated successfully"}