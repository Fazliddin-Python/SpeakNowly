from fastapi import APIRouter, HTTPException, status
from ...serializers.users.login import LoginSerializer, AuthSerializer
from models.users.users import User
from utils.auth import create_access_token  # Import the function

router = APIRouter()

@router.post("/login/", response_model=AuthSerializer, status_code=status.HTTP_200_OK)
async def login(data: LoginSerializer):
    """
    Authenticate a user and return a token.
    """
    # Check if the user exists
    user = await User.get_or_none(email=data.email)
    if not user or not user.check_password(data.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # Generate a JWT token
    token = create_access_token({"sub": user.email})

    return {"token": token, "auth_type": "Bearer"}