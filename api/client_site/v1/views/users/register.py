from fastapi import APIRouter, HTTPException, status
from ..serializers.register import RegisterSerializer

router = APIRouter()


@router.post("/register/", status_code=status.HTTP_201_CREATED)
async def register(data: RegisterSerializer):
    """
    Register a new user.
    """
    if await User.filter(email=data.email).exists():
        raise HTTPException(status_code=400, detail="Email is already registered")
    user = User(email=data.email)
    user.set_password(data.password)
    await user.save()
    return {"message": "User registered successfully"}