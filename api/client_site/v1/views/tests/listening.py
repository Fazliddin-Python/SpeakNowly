from fastapi import APIRouter, HTTPException
from models.tests.listening import Listening, ListeningPart1, ListeningPart2, ListeningPart3
from api.client_site.v1.serializers.tests.listening import (
    ListeningSerializer,
    ListeningPart1Serializer,
    ListeningPart2Serializer,
    ListeningPart3Serializer,
)

router = APIRouter()

# Listening endpoints
@router.get("/", response_model=list[ListeningSerializer])
async def get_listening_tests():
    tests = await Listening.all()
    return tests


@router.get("/{test_id}/", response_model=ListeningSerializer)
async def get_listening_test(test_id: int):
    test = await Listening.get_or_none(id=test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Listening test not found")
    return test


@router.post("/", response_model=ListeningSerializer)
async def create_listening_test(data: ListeningSerializer):
    test = await Listening.create(**data.dict())
    return test


@router.delete("/{test_id}/")
async def delete_listening_test(test_id: int):
    test = await Listening.get_or_none(id=test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Listening test not found")
    await test.delete()
    return {"message": "Listening test deleted successfully"}


# ListeningPart1 endpoints
@router.get("/part1/", response_model=list[ListeningPart1Serializer])
async def get_listening_part1():
    parts = await ListeningPart1.all()
    return parts


@router.post("/part1/", response_model=ListeningPart1Serializer)
async def create_listening_part1(data: ListeningPart1Serializer):
    part = await ListeningPart1.create(**data.dict())
    return part


# ListeningPart2 endpoints
@router.get("/part2/", response_model=list[ListeningPart2Serializer])
async def get_listening_part2():
    parts = await ListeningPart2.all()
    return parts


@router.post("/part2/", response_model=ListeningPart2Serializer)
async def create_listening_part2(data: ListeningPart2Serializer):
    part = await ListeningPart2.create(**data.dict())
    return part


# ListeningPart3 endpoints
@router.get("/part3/", response_model=list[ListeningPart3Serializer])
async def get_listening_part3():
    parts = await ListeningPart3.all()
    return parts


@router.post("/part3/", response_model=ListeningPart3Serializer)
async def create_listening_part3(data: ListeningPart3Serializer):
    part = await ListeningPart3.create(**data.dict())
    return part