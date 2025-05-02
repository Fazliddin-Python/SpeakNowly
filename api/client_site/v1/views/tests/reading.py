from fastapi import APIRouter, HTTPException
from models.tests.reading import Reading, ReadingPart1, ReadingPart2, ReadingPart3
from api.client_site.v1.serializers.tests.reading import (
    ReadingSerializer,
    ReadingPart1Serializer,
    ReadingPart2Serializer,
    ReadingPart3Serializer,
)

router = APIRouter()

# Reading endpoints
@router.get("/", response_model=list[ReadingSerializer])
async def get_reading_tests():
    tests = await Reading.all()
    return tests


@router.get("/{test_id}/", response_model=ReadingSerializer)
async def get_reading_test(test_id: int):
    test = await Reading.get_or_none(id=test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Reading test not found")
    return test


@router.post("/", response_model=ReadingSerializer)
async def create_reading_test(data: ReadingSerializer):
    test = await Reading.create(**data.dict())
    return test


@router.delete("/{test_id}/")
async def delete_reading_test(test_id: int):
    test = await Reading.get_or_none(id=test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Reading test not found")
    await test.delete()
    return {"message": "Reading test deleted successfully"}


# ReadingPart1 endpoints
@router.get("/part1/", response_model=list[ReadingPart1Serializer])
async def get_reading_part1():
    parts = await ReadingPart1.all()
    return parts


@router.post("/part1/", response_model=ReadingPart1Serializer)
async def create_reading_part1(data: ReadingPart1Serializer):
    part = await ReadingPart1.create(**data.dict())
    return part


# ReadingPart2 endpoints
@router.get("/part2/", response_model=list[ReadingPart2Serializer])
async def get_reading_part2():
    parts = await ReadingPart2.all()
    return parts


@router.post("/part2/", response_model=ReadingPart2Serializer)
async def create_reading_part2(data: ReadingPart2Serializer):
    part = await ReadingPart2.create(**data.dict())
    return part


# ReadingPart3 endpoints
@router.get("/part3/", response_model=list[ReadingPart3Serializer])
async def get_reading_part3():
    parts = await ReadingPart3.all()
    return parts


@router.post("/part3/", response_model=ReadingPart3Serializer)
async def create_reading_part3(data: ReadingPart3Serializer):
    part = await ReadingPart3.create(**data.dict())
    return part