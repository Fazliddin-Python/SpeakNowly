from fastapi import APIRouter, HTTPException, Depends, status
from typing import List
from services.tests.listening_service import ListeningService
from ...serializers.tests.listening import (
    ListeningSerializer,
    ListeningPartSerializer,
    ListeningSectionSerializer,
    ListeningQuestionSerializer,
    UserListeningSessionSerializer,
    UserResponseSerializer,
)
from utils.i18n import get_translation
from utils.auth.auth import get_current_user

router = APIRouter()

@router.get("/", response_model=List[ListeningSerializer])
async def get_listening_tests(
    user=Depends(get_current_user),
    t: dict = Depends(get_translation)
):
    """Retrieve all listening tests."""
    return await ListeningService.list_tests()

@router.get("/{test_id}/", response_model=ListeningSerializer)
async def get_listening_test(
    test_id: int,
    user=Depends(get_current_user),
    t: dict = Depends(get_translation)
):
    """Retrieve a specific listening test by ID."""
    test = await ListeningService.get_test(test_id)
    if not test:
        raise HTTPException(status_code=404, detail=t["listening_test_not_found"])
    return test

@router.post("/", response_model=ListeningSerializer, status_code=status.HTTP_201_CREATED)
async def create_listening_test(
    data: ListeningSerializer,
    user=Depends(get_current_user)
):
    """Create a new listening test."""
    return await ListeningService.create_test(data.dict())

@router.delete("/{test_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_listening_test(
    test_id: int,
    user=Depends(get_current_user)
):
    """Delete a specific listening test by ID."""
    ok = await ListeningService.delete_test(test_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Listening test not found")
    return {"message": "Listening test deleted successfully"}

@router.post("/start/", response_model=UserListeningSessionSerializer, status_code=status.HTTP_201_CREATED)
async def start_listening_test(
    user=Depends(get_current_user),
    t: dict = Depends(get_translation)
):
    """Start a new listening test session for a user."""
    session = await ListeningService.start_session(user.id)
    if not session:
        raise HTTPException(status_code=404, detail=t["no_listening_tests"])
    return session

@router.get("/session/{session_id}/", response_model=UserListeningSessionSerializer)
async def get_listening_session(
    session_id: int,
    user=Depends(get_current_user),
    t: dict = Depends(get_translation)
):
    """Retrieve details of a specific listening session by ID."""
    session = await ListeningService.get_session(session_id)
    if not session or session.user_id != user.id:
        raise HTTPException(status_code=404, detail=t["listening_session_not_found"])
    return session

@router.post("/session/{session_id}/submit/", status_code=status.HTTP_201_CREATED)
async def submit_listening_answers(
    session_id: int,
    answers: List[UserResponseSerializer],
    user=Depends(get_current_user),
    t: dict = Depends(get_translation)
):
    """Submit answers for a listening test session."""
    total_score, error = await ListeningService.submit_answers(session_id, user.id, [a.dict() for a in answers])
    if error == "not_found":
        raise HTTPException(status_code=404, detail=t["listening_session_not_found"])
    if error == "already_completed":
        raise HTTPException(status_code=400, detail=t["session_already_completed"])
    if error and error.startswith("question_"):
        raise HTTPException(status_code=404, detail=t["question_not_found"])
    return {"message": t["answers_submitted"], "total_score": total_score}

@router.post("/session/{session_id}/cancel/", status_code=status.HTTP_200_OK)
async def cancel_listening_session(
    session_id: int,
    user=Depends(get_current_user),
    t: dict = Depends(get_translation)
):
    """Cancel a listening test session."""
    ok = await ListeningService.cancel_session(session_id, user.id)
    if not ok:
        raise HTTPException(status_code=404, detail=t["listening_session_not_found"])
    return {"message": t["session_cancelled"]}

# --- CRUD for parts, sections, questions ---

@router.get("/part/{part_id}/", response_model=ListeningPartSerializer)
async def get_listening_part(
    part_id: int,
    user=Depends(get_current_user),
    t: dict = Depends(get_translation)
):
    part = await ListeningService.get_part(part_id)
    if not part:
        raise HTTPException(status_code=404, detail=t["listening_part_not_found"])
    return part

@router.get("/sections/", response_model=List[ListeningSectionSerializer])
async def get_listening_sections(
    user=Depends(get_current_user),
    t: dict = Depends(get_translation)
):
    return await ListeningService.list_sections()

@router.get("/sections/{section_id}/", response_model=ListeningSectionSerializer)
async def get_listening_section(
    section_id: int,
    user=Depends(get_current_user),
    t: dict = Depends(get_translation)
):
    section = await ListeningService.get_section(section_id)
    if not section:
        raise HTTPException(status_code=404, detail=t["listening_section_not_found"])
    return section

@router.post("/sections/", response_model=ListeningSectionSerializer, status_code=201)
async def create_listening_section(
    data: ListeningSectionSerializer,
    user=Depends(get_current_user)
):
    return await ListeningService.create_section(data.dict())

@router.delete("/sections/{section_id}/", status_code=204)
async def delete_listening_section(
    section_id: int,
    user=Depends(get_current_user)
):
    ok = await ListeningService.delete_section(section_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Listening section not found")
    return {"message": "Listening section deleted successfully"}

@router.get("/questions/", response_model=List[ListeningQuestionSerializer])
async def get_listening_questions(
    user=Depends(get_current_user),
    t: dict = Depends(get_translation)
):
    return await ListeningService.list_questions()

@router.get("/questions/{question_id}/", response_model=ListeningQuestionSerializer)
async def get_listening_question(
    question_id: int,
    user=Depends(get_current_user),
    t: dict = Depends(get_translation)
):
    question = await ListeningService.get_question(question_id)
    if not question:
        raise HTTPException(status_code=404, detail=t["listening_question_not_found"])
    return question

@router.post("/questions/", response_model=ListeningQuestionSerializer, status_code=status.HTTP_201_CREATED)
async def create_listening_question(
    data: ListeningQuestionSerializer,
    user=Depends(get_current_user)
):
    return await ListeningService.create_question(data.dict())

@router.delete("/questions/{question_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_listening_question(
    question_id: int,
    user=Depends(get_current_user)
):
    ok = await ListeningService.delete_question(question_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Listening question not found")
    return {"message": "Listening question deleted successfully"}