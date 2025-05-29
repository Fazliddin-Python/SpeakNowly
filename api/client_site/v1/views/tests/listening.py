from fastapi import APIRouter, HTTPException, Depends, status, Request
from typing import List
import asyncio
import logging

from services.tests.listening_service import ListeningService
from ...serializers.tests.listening import (
    ListeningSerializer,
    ListeningCreateSerializer,
    ListeningPartSerializer,
    ListeningPartCreateSerializer,
    ListeningSectionSerializer,
    ListeningSectionCreateSerializer,
    ListeningQuestionSerializer,
    ListeningQuestionCreateSerializer,
    UserListeningSessionSerializer,
    UserResponseSerializer,
    UserResponseCreateSerializer,
    ListeningDataSerializer,
    ListeningAnswerSerializer,
    ListeningAnalyseResponseSerializer,
)
from utils.auth.auth import get_current_user
from utils.i18n import get_translation

logger = logging.getLogger(__name__)
router = APIRouter()

def audit_action(action: str):
    def wrapper(request: Request, user=Depends(get_current_user)):
        logger.info(f"User {user.id} action: {action} path: {request.url.path}")
        return user
    return wrapper

def admin_required(user=Depends(get_current_user)):
    if not user.is_staff or not user.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")
    return user

# --- Listening Tests ---
@router.get("/tests", response_model=List[ListeningSerializer], summary="List all listening tests")
async def list_listening_tests(
    user=Depends(get_current_user),
    t: dict = Depends(get_translation),
    _: any = Depends(audit_action("list_listening_tests")),
):
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=t["inactive_user"])
    tests = await ListeningService.list_tests()
    return await asyncio.gather(*[ListeningSerializer.from_orm(test) for test in tests])

@router.get("/tests/{test_id}", response_model=ListeningSerializer, summary="Get a listening test by ID")
async def retrieve_listening_test(
    test_id: int,
    user=Depends(get_current_user),
    t: dict = Depends(get_translation),
    _: any = Depends(audit_action("retrieve_listening_test")),
):
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=t["inactive_user"])
    test = await ListeningService.get_test(test_id)
    return await ListeningSerializer.from_orm(test)

@router.post("/tests", response_model=ListeningSerializer, status_code=status.HTTP_201_CREATED, summary="Create a new listening test")
async def create_listening_test(
    payload: ListeningCreateSerializer,
    _: any = Depends(admin_required),
    __: any = Depends(audit_action("create_listening_test")),
):
    """
    Create a new listening test (admin only).
    """
    test = await ListeningService.create_test(payload.dict())
    return await ListeningSerializer.from_orm(test)

@router.delete("/tests/{test_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a listening test")
async def delete_listening_test(
    test_id: int,
    _: any = Depends(admin_required),
    __: any = Depends(audit_action("delete_listening_test")),
):
    await ListeningService.delete_test(test_id)

# --- Listening Parts ---
@router.get("/parts/{part_id}", response_model=ListeningPartSerializer, summary="Get listening part")
async def get_listening_part(
    part_id: int,
    user=Depends(get_current_user),
    t: dict = Depends(get_translation),
    _: any = Depends(audit_action("get_listening_part")),
):
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=t["inactive_user"])
    part = await ListeningService.get_part(part_id)
    return await ListeningPartSerializer.from_orm(part)

@router.post("/parts", response_model=ListeningPartSerializer, status_code=status.HTTP_201_CREATED, summary="Create listening part")
async def create_listening_part(
    payload: ListeningPartCreateSerializer,
    _: any = Depends(admin_required),
    __: any = Depends(audit_action("create_listening_part")),
):
    """
    Create a new listening test part (admin only).
    """
    part = await ListeningService.create_part(payload.dict())
    return await ListeningPartSerializer.from_orm(part)

# --- Listening Sections ---
@router.get("/sections", response_model=List[ListeningSectionSerializer], summary="List all sections")
async def list_listening_sections(
    user=Depends(get_current_user),
    t: dict = Depends(get_translation),
    _: any = Depends(audit_action("list_listening_sections")),
):
    """
    Retrieve all listening sections.
    """
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=t["inactive_user"])
    sections = await ListeningService.list_sections()
    return await asyncio.gather(*[ListeningSectionSerializer.from_orm(sec) for sec in sections])

@router.get("/sections/{section_id}", response_model=ListeningSectionSerializer, summary="Get listening section")
async def get_listening_section(
    section_id: int,
    user=Depends(get_current_user),
    t: dict = Depends(get_translation),
    _: any = Depends(audit_action("get_listening_section")),
):
    """
    Retrieve a listening section by ID.
    """
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=t["inactive_user"])
    section = await ListeningService.get_section(section_id)
    return await ListeningSectionSerializer.from_orm(section)

@router.post("/sections", response_model=ListeningSectionSerializer, status_code=status.HTTP_201_CREATED, summary="Create listening section")
async def create_listening_section(
    payload: ListeningSectionCreateSerializer,
    _: any = Depends(admin_required),
    __: any = Depends(audit_action("create_listening_section")),
):
    """
    Create a listening section (admin only).
    """
    section = await ListeningService.create_section(payload.dict())
    return await ListeningSectionSerializer.from_orm(section)

@router.delete("/sections/{section_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete listening section")
async def delete_listening_section(
    section_id: int,
    _: any = Depends(admin_required),
    __: any = Depends(audit_action("delete_listening_section")),
):
    """
    Delete a listening section by ID (admin only).
    """
    await ListeningService.delete_section(section_id)

# --- Listening Questions ---
@router.get("/questions", response_model=List[ListeningQuestionSerializer], summary="List all questions")
async def list_listening_questions(
    user=Depends(get_current_user),
    t: dict = Depends(get_translation),
    _: any = Depends(audit_action("list_listening_questions")),
):
    """
    Retrieve all listening questions.
    """
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=t["inactive_user"])
    questions = await ListeningService.list_questions()
    return await asyncio.gather(*[ListeningQuestionSerializer.from_orm(q) for q in questions])

@router.get("/questions/{question_id}", response_model=ListeningQuestionSerializer, summary="Get listening question")
async def get_listening_question(
    question_id: int,
    user=Depends(get_current_user),
    t: dict = Depends(get_translation),
    _: any = Depends(audit_action("get_listening_question")),
):
    """
    Retrieve a listening question by ID.
    """
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=t["inactive_user"])
    question = await ListeningService.get_question(question_id)
    return await ListeningQuestionSerializer.from_orm(question)

@router.post("/questions", response_model=ListeningQuestionSerializer, status_code=status.HTTP_201_CREATED, summary="Create listening question")
async def create_listening_question(
    payload: ListeningQuestionCreateSerializer,
    _: any = Depends(admin_required),
    __: any = Depends(audit_action("create_listening_question")),
):
    question = await ListeningService.create_question(payload.dict())
    return await ListeningQuestionSerializer.from_orm(question)

@router.delete("/questions/{question_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete listening question")
async def delete_listening_question(
    question_id: int,
    _: any = Depends(admin_required),
    __: any = Depends(audit_action("delete_listening_question")),
):
    """
    Delete a listening question by ID (admin only).
    """
    await ListeningService.delete_question(question_id)

# --- User Listening Sessions ---
@router.post("/session", response_model=UserListeningSessionSerializer, status_code=status.HTTP_201_CREATED, summary="Start a new listening session")
async def start_listening_session(
    user=Depends(get_current_user),
    t: dict = Depends(get_translation),
    _: any = Depends(audit_action("start_listening_session")),
):
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=t["inactive_user"])
    session = await ListeningService.start_session(user.id)
    return await UserListeningSessionSerializer.from_orm(session)

@router.get("/session/{session_id}", response_model=UserListeningSessionSerializer, summary="Get session details")
async def get_listening_session(
    session_id: int,
    user=Depends(get_current_user),
    t: dict = Depends(get_translation),
    _: any = Depends(audit_action("get_listening_session")),
):
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=t["inactive_user"])
    session = await ListeningService.get_session(session_id, user.id)
    return await UserListeningSessionSerializer.from_orm(session)

@router.post("/session/{session_id}/cancel", status_code=status.HTTP_200_OK, summary="Cancel listening session")
async def cancel_listening_session(
    session_id: int,
    user=Depends(get_current_user),
    t: dict = Depends(get_translation),
    _: any = Depends(audit_action("cancel_listening_session")),
):
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=t["inactive_user"])
    await ListeningService.cancel_session(session_id, user.id)
    return {"detail": t["session_cancelled"]}

@router.get("/session/{session_id}/data", response_model=ListeningDataSerializer)
async def get_listening_data(
    session_id: int,
    user=Depends(get_current_user),
):
    data = await ListeningService.get_session_data(session_id, user.id)
    return data

@router.post("/session/{session_id}/submit", status_code=status.HTTP_200_OK)
async def submit_listening_answers(
    session_id: int,
    payload: ListeningAnswerSerializer,
    user=Depends(get_current_user),
):
    await ListeningService.submit_answers(session_id, user.id, payload.dict())
    return {"detail": "Answers submitted"}

@router.get("/session/{session_id}/analyse", response_model=ListeningAnalyseResponseSerializer)
async def get_listening_analysis(
    session_id: int,
    user=Depends(get_current_user),
):
    data = await ListeningService.get_analysis(session_id, user.id)
    return data
