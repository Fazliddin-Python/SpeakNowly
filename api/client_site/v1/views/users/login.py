from fastapi import APIRouter, HTTPException, status
from ...serializers.users.login import LoginSerializer, AuthSerializer
from models.users.users import User
from utils.auth import create_access_token

router = APIRouter()

@router.post("/login/", response_model=AuthSerializer, status_code=status.HTTP_200_OK)
async def login(data: LoginSerializer) -> AuthSerializer:
    """
    Authenticate a user and return a token.
    """
    user = await User.get_or_none(email=data.email)
    if not user or not user.check_password(data.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not user.is_verified:
        # raise HTTPException(status_code=403, detail="Email not verified")
        pass

    token = create_access_token({"sub": str(user.id), "email": user.email})
    return AuthSerializer(token=token, auth_type="Bearer")
