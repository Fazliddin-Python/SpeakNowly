import random
from fastapi import APIRouter, HTTPException, status
from ...serializers.users.register import RegisterSerializer, RegisterResponseSerializer
from models.users.users import User
from models.users.verification_codes import VerificationCode, VerificationType
from utils.auth import create_access_token

router = APIRouter()


@router.post("/register/", response_model=RegisterResponseSerializer, status_code=status.HTTP_201_CREATED)
async def register(data: RegisterSerializer) -> RegisterResponseSerializer:
    """
    Register a new user and send a verification code.
    """
    if await User.filter(email=data.email, is_verified=True).exists():
        raise HTTPException(status_code=400, detail="This email is already registered")

    user = User(email=data.email)
    user.set_password(data.password)
    await user.save()

    if await VerificationCode.is_resend_blocked(data.email, VerificationType.REGISTER):
        raise HTTPException(status_code=429, detail="Too many requests. Please try again later.")

    code = random.randint(10000, 99999)
    await VerificationCode.update_or_create(
        user_id=user.id,
        email=data.email,
        verification_type=VerificationType.REGISTER,
        defaults={"code": code, "is_used": False, "is_expired": False},
    )

    token = create_access_token({"sub": str(user.id), "email": user.email})

    return RegisterResponseSerializer(message="User registered successfully", token=token)
