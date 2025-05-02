from fastapi import APIRouter, HTTPException
from models.tests.speaking import Speaking, SpeakingPart1, SpeakingPart2, SpeakingPart3
from api.client_site.v1.serializers.tests.speaking import (
    SpeakingSerializer,
    SpeakingPart1Serializer,
    SpeakingPart2Serializer,
    SpeakingPart3Serializer,
)

router = APIRouter()

# Speaking endpoints
@router.get("/", response_model=list[SpeakingSerializer])
async def get_speaking_tests():
    tests = await Speaking.all()
    return tests


@router.get("/{test_id}/", response_model=SpeakingSerializer)
async def get_speaking_test(test_id: int):
    test = await Speaking.get_or_none(id=test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Speaking test not found")
    return test


@router.post("/", response_model=SpeakingSerializer)
async def create_speaking_test(data: SpeakingSerializer):
    test = await Speaking.create(**data.dict())
    return test


@router.delete("/{test_id}/")
async def delete_speaking_test(test_id: int):
    test = await Speaking.get_or_none(id=test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Speaking test not found")
    await test.delete()
    return {"message": "Speaking test deleted successfully"}


# SpeakingPart1 endpoints
@router.get("/part1/", response_model=list[SpeakingPart1Serializer])
async def get_speaking_part1():
    parts = await SpeakingPart1.all()
    return parts


@router.post("/part1/", response_model=SpeakingPart1Serializer)
async def create_speaking_part1(data: SpeakingPart1Serializer):
    part = await SpeakingPart1.create(**data.dict())
    return part


# SpeakingPart2 endpoints
@router.get("/part2/", response_model=list[SpeakingPart2Serializer])
async def get_speaking_part2():
    parts = await SpeakingPart2.all()
    return parts


@router.post("/part2/", response_model=SpeakingPart2Serializer)
async def create_speaking_part2(data: SpeakingPart2Serializer):
    part = await SpeakingPart2.create(**data.dict())
    return part


# SpeakingPart3 endpoints
@router.get("/part3/", response_model=list[SpeakingPart3Serializer])
async def get_speaking_part3():
    parts = await SpeakingPart3.all()
    return parts


@router.post("/part3/", response_model=SpeakingPart3Serializer)
async def create_speaking_part3(data: SpeakingPart3Serializer):
    part = await SpeakingPart3.create(**data.dict())
    return part