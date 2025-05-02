from fastapi import APIRouter, HTTPException
from models.users import User, VerificationCode
from api.client_site.v1.serializers.users import (
    UserSerializer,
    UserCreateSerializer,
    UserUpdateSerializer,
    VerificationCodeSerializer,
)

router = APIRouter()

@router.get("/", response_model=list[UserSerializer])
async def get_users():
    users = await User.all()
    return users

@router.post("/", response_model=UserSerializer)
async def create_user(user_data: UserCreateSerializer):
    user = User(**user_data.dict())
    user.set_password(user_data.password)
    await user.save()
    return user

@router.put("/{user_id}/", response_model=UserSerializer)
async def update_user(user_id: int, user_data: UserUpdateSerializer):
    user = await User.get_or_none(id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.update_from_dict(user_data.dict(exclude_unset=True))
    await user.save()
    return user

@router.delete("/{user_id}/")
async def delete_user(user_id: int):
    user = await User.get_or_none(id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await user.delete()
    return {"message": "User deleted successfully"}

@router.get("/verification-codes/", response_model=list[VerificationCodeSerializer])
async def get_verification_codes():
    codes = await VerificationCode.all()
    return codes

@router.post("/verification-codes/", response_model=VerificationCodeSerializer)
async def create_verification_code(data: VerificationCodeSerializer):
    code = await VerificationCode.create(**data.dict())
    return code

@router.get("/verification-codes/{code_id}/", response_model=VerificationCodeSerializer)
async def get_verification_code(code_id: int):
    code = await VerificationCode.get_or_none(id=code_id)
    if not code:
        raise HTTPException(status_code=404, detail="Verification code not found")
    return code

@router.delete("/verification-codes/{code_id}/")
async def delete_verification_code(code_id: int):
    code = await VerificationCode.get_or_none(id=code_id)
    if not code:
        raise HTTPException(status_code=404, detail="Verification code not found")
    await code.delete()
    return {"message": "Verification code deleted successfully"}