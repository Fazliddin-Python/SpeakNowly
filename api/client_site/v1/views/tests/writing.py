from fastapi import APIRouter, HTTPException
from models.tests.writing import Writing, WritingPart1, WritingPart2
from api.client_site.v1.serializers.tests.writing import (
    WritingSerializer,
    WritingPart1Serializer,
    WritingPart2Serializer,
)

router = APIRouter()

# Writing endpoints
@router.get("/", response_model=list[WritingSerializer])
async def get_writing_tests():
    tests = await Writing.all()
    return tests


@router.get("/{test_id}/", response_model=WritingSerializer)
async def get_writing_test(test_id: int):
    test = await Writing.get_or_none(id=test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Writing test not found")
    return test


@router.post("/", response_model=WritingSerializer)
async def create_writing_test(data: WritingSerializer):
    test = await Writing.create(**data.dict())
    return test


@router.delete("/{test_id}/")
async def delete_writing_test(test_id: int):
    test = await Writing.get_or_none(id=test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Writing test not found")
    await test.delete()
    return {"message": "Writing test deleted successfully"}


# WritingPart1 endpoints
@router.get("/part1/", response_model=list[WritingPart1Serializer])
async def get_writing_part1():
    parts = await WritingPart1.all()
    return parts


@router.post("/part1/", response_model=WritingPart1Serializer)
async def create_writing_part1(data: WritingPart1Serializer):
    part = await WritingPart1.create(**data.dict())
    return part


# WritingPart2 endpoints
@router.get("/part2/", response_model=list[WritingPart2Serializer])
async def get_writing_part2():
    parts = await WritingPart2.all()
    return parts


@router.post("/part2/", response_model=WritingPart2Serializer)
async def create_writing_part2(data: WritingPart2Serializer):
    part = await WritingPart2.create(**data.dict())
    return part