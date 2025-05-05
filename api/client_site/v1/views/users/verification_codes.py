from fastapi import APIRouter, HTTPException, status
from typing import List
from models.users import VerificationCode
from ...serializers.users import VerificationCodeSerializer

router = APIRouter()

@router.get("/", response_model=List[VerificationCodeSerializer])
async def get_verification_codes():
    """
    Retrieve a list of all verification codes.
    """
    codes = await VerificationCode.all()
    if not codes:
        raise HTTPException(status_code=404, detail="No verification codes found")
    return codes


@router.post("/", response_model=VerificationCodeSerializer, status_code=status.HTTP_201_CREATED)
async def create_verification_code(data: VerificationCodeSerializer):
    """
    Create a new verification code.
    """
    if await VerificationCode.filter(email=data.email, verification_type=data.verification_type, is_used=False).exists():
        raise HTTPException(status_code=400, detail="A verification code already exists for this email")
    code = await VerificationCode.create(**data.dict())
    return code


@router.get("/{code_id}/", response_model=VerificationCodeSerializer)
async def get_verification_code(code_id: int):
    """
    Retrieve a specific verification code by ID.
    """
    code = await VerificationCode.get_or_none(id=code_id)
    if not code:
        raise HTTPException(status_code=404, detail="Verification code not found")
    return code


@router.delete("/{code_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_verification_code(code_id: int):
    """
    Delete a verification code by ID.
    """
    code = await VerificationCode.get_or_none(id=code_id)
    if not code:
        raise HTTPException(status_code=404, detail="Verification code not found")
    await code.delete()
    return {"message": "Verification code deleted successfully"}