from fastapi import APIRouter, HTTPException, Depends, status
from typing import List
from tortoise.exceptions import DoesNotExist
from models.tests.listening import (
    Listening,
    ListeningPart,
    ListeningSection,
    ListeningQuestion,
    UserListeningSession,
    UserResponse,
)
from ...serializers.tests.listening import (
    ListeningSerializer,
    ListeningPartSerializer,
    ListeningSectionSerializer,
    ListeningQuestionSerializer,
    UserListeningSessionSerializer,
    UserResponseSerializer,
)
from datetime import datetime
import random

router = APIRouter()


@router.get("/", response_model=List[ListeningSerializer])
async def get_listening_tests():
    """
    Retrieve all listening tests.
    """
    tests = await Listening.all()
    if not tests:
        raise HTTPException(status_code=404, detail="No listening tests found")
    return tests


@router.get("/{test_id}/", response_model=ListeningSerializer)
async def get_listening_test(test_id: int):
    """
    Retrieve a specific listening test by ID.
    """
    test = await Listening.get_or_none(id=test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Listening test not found")
    return test


@router.post("/", response_model=ListeningSerializer, status_code=status.HTTP_201_CREATED)
async def create_listening_test(data: ListeningSerializer):
    """
    Create a new listening test.
    """
    test = await Listening.create(**data.dict())
    return test


@router.delete("/{test_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_listening_test(test_id: int):
    """
    Delete a specific listening test by ID.
    """
    test = await Listening.get_or_none(id=test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Listening test not found")
    await test.delete()
    return {"message": "Listening test deleted successfully"}


@router.post("/start/", response_model=UserListeningSessionSerializer, status_code=status.HTTP_201_CREATED)
async def start_listening_test(user_id: int):
    """
    Start a new listening test session for a user.
    """
    listening_tests = await Listening.all()
    if not listening_tests:
        raise HTTPException(status_code=404, detail="No listening tests available")

    selected_test = random.choice(listening_tests)
    session = await UserListeningSession.create(
        user_id=user_id,
        exam_id=selected_test.id,
        start_time=datetime.utcnow(),
        status="started",
    )
    return session


@router.get("/session/{session_id}/", response_model=UserListeningSessionSerializer)
async def get_listening_session(session_id: int):
    """
    Retrieve details of a specific listening session by ID.
    """
    session = await UserListeningSession.get_or_none(id=session_id).prefetch_related("exam")
    if not session:
        raise HTTPException(status_code=404, detail="Listening session not found")
    return session


@router.post("/session/{session_id}/submit/", status_code=status.HTTP_201_CREATED)
async def submit_listening_answers(session_id: int, answers: List[UserResponseSerializer]):
    """
    Submit answers for a listening test session.
    """
    session = await UserListeningSession.get_or_none(id=session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Listening session not found")

    if session.status == "completed":
        raise HTTPException(status_code=400, detail="This session has already been completed")

    total_score = 0
    answered_question_ids = []

    for answer in answers:
        question = await ListeningQuestion.get_or_none(id=answer.question_id)
        if not question:
            raise HTTPException(status_code=404, detail=f"Question {answer.question_id} not found")

        is_correct = question.correct_answer == answer.user_answer
        score = 1 if is_correct else 0
        total_score += score

        await UserResponse.create(
            session_id=session_id,
            user_id=session.user_id,
            question_id=answer.question_id,
            user_answer=answer.user_answer,
            is_correct=is_correct,
            score=score,
        )
        answered_question_ids.append(answer.question_id)

    # Handle unanswered questions
    all_questions = await ListeningQuestion.filter(section__part__listening_id=session.exam_id).all()
    unanswered_questions = [q for q in all_questions if q.id not in answered_question_ids]

    for question in unanswered_questions:
        await UserResponse.create(
            session_id=session_id,
            user_id=session.user_id,
            question_id=question.id,
            user_answer=None,
            is_correct=False,
            score=0,
        )

    session.status = "completed"
    session.end_time = datetime.utcnow()
    await session.save()

    return {"message": "Answers submitted successfully", "total_score": total_score}


@router.post("/session/{session_id}/cancel/", status_code=status.HTTP_200_OK)
async def cancel_listening_session(session_id: int):
    """
    Cancel a listening test session.
    """
    session = await UserListeningSession.get_or_none(id=session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Listening session not found")

    if session.status in ["completed", "cancelled"]:
        raise HTTPException(status_code=400, detail="Session cannot be cancelled")

    session.status = "cancelled"
    await session.save()
    return {"message": "Session cancelled successfully"}


@router.get("/part/{part_id}/", response_model=ListeningPartSerializer)
async def get_listening_part(part_id: int):
    """
    Retrieve details of a specific listening part by ID.
    """
    part = await ListeningPart.get_or_none(id=part_id).prefetch_related("sections")
    if not part:
        raise HTTPException(status_code=404, detail="Listening part not found")
    return part