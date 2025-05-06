import random
from fastapi import APIRouter, HTTPException, status
from ...serializers.users.register import RegisterSerializer, RegisterResponseSerializer
from models.users.users import User
from models.users.verification_codes import VerificationCode
from utils.auth import create_access_token  # Import the function

router = APIRouter()


@router.post("/register/", response_model=RegisterResponseSerializer, status_code=status.HTTP_201_CREATED)
async def register(data: RegisterSerializer):
    """
    Register a new user and send a verification code.
    """
    # Check if the email is already registered
    if await User.filter(email=data.email, is_verified=True).exists():
        raise HTTPException(status_code=400, detail="This email is already registered")

    # Create or get the user
    user, created = await User.get_or_create(email=data.email)
    user.set_password(data.password)
    await user.save()

    # Check resend limit for verification code
    if await VerificationCode.is_resend_blocked(data.email, VerificationCode.REGISTER):
        raise HTTPException(status_code=429, detail="Too many requests. Please try again later.")

    # Generate and save the verification code
    code = random.randint(10000, 99999)
    await VerificationCode.update_or_create(
        user_id=user.id,
        email=data.email,
        verification_type=VerificationCode.REGISTER,
        defaults={"code": code, "is_used": False, "is_expired": False},
    )

    # Generate a JWT token for the user
    token = create_access_token({"sub": user.email})

    return {"message": "User registered successfully", "token": token}