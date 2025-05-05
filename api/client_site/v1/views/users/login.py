from fastapi import APIRouter, HTTPException, status
from ..serializers.login import LoginSerializer, AuthSerializer

router = APIRouter()


@router.post("/login/", response_model=AuthSerializer, status_code=status.HTTP_200_OK)
async def login(data: LoginSerializer):
    """
    Authenticate a user and return a token.
    """
    user = await User.get_or_none(email=data.email)
    if not user or not user.check_password(data.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    # Simulate token generation
    token = "example_token"
    return {"token": token, "auth_type": "Bearer"}