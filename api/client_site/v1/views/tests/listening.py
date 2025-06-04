from fastapi import APIRouter, Form, HTTPException, Depends, status, Request, UploadFile, File
from typing import List, Any
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
    ListeningDataSlimSerializer,
    ListeningAnswerSerializer,
    ListeningAnalyseResponseSerializer,
)
from utils.auth.auth import get_current_user
from utils.i18n import get_translation

logger = logging.getLogger(__name__)
router = APIRouter()


def audit_action(action: str):
    """
    Dependency factory: logs user action and returns the user object.
    """
    def wrapper(request: Request, user=Depends(get_current_user)):
        logger.info(f"User {user.id} action='{action}' path='{request.url.path}'")
        return user
    return wrapper


def active_user(user=Depends(get_current_user), t=Depends(get_translation)):
    """
    Ensures the user is active.
    """
    if not user.is_active:
        logger.warning(f"Inactive user (id={user.id}) attempted access")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=t["inactive_user"])
    return user


def admin_required(user=Depends(get_current_user), t=Depends(get_translation)):
    """
    Ensures the user has admin privileges.
    """
    if not (user.is_staff and user.is_superuser):
        logger.warning(f"Permission denied for user_id={user.id}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=t["permission_denied"])
    return user


@router.get("/tests", response_model=List[ListeningSerializer], summary="List all listening tests")
async def list_listening_tests(
    user=Depends(active_user),
    t: dict = Depends(get_translation),
    _: Any = Depends(audit_action("list_listening_tests")),
):
    """
    Retrieve all listening tests with nested parts, sections, and questions.
    (This endpoint is admin‐only if parts/questions include correct answers;
     otherwise, adjust accordingly.)
    """
    logger.info(f"Retrieving all listening tests for user {user.id}")
    tests = await ListeningService.list_tests()
    return await asyncio.gather(*[ListeningSerializer.from_orm(test) for test in tests])


@router.get("/tests/{test_id}", response_model=ListeningSerializer, summary="Get a listening test by ID")
async def retrieve_listening_test(
    test_id: int,
    user=Depends(active_user),
    t: dict = Depends(get_translation),
    _: Any = Depends(audit_action("retrieve_listening_test")),
):
    """
    Retrieve a specific listening test by its ID.
    """
    logger.info(f"Retrieving listening test id={test_id} for user {user.id}")
    test = await ListeningService.get_test(test_id, t=t)
    return await ListeningSerializer.from_orm(test)


@router.post(
    "/tests",
    response_model=ListeningSerializer,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new listening test",
)
async def create_listening_test(
    payload: ListeningCreateSerializer,
    _: Any = Depends(admin_required),
    t: dict = Depends(get_translation),
    __: Any = Depends(audit_action("create_listening_test")),
):
    """
    Create a new listening test. Requires admin privileges.
    """
    logger.info("Admin creating a new listening test")
    test = await ListeningService.create_test(payload.dict())
    return await ListeningSerializer.from_orm(test)


@router.delete(
    "/tests/{test_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a listening test",
)
async def delete_listening_test(
    test_id: int,
    _: Any = Depends(admin_required),
    t: dict = Depends(get_translation),
    __: Any = Depends(audit_action("delete_listening_test")),
):
    """
    Delete a listening test by its ID. Requires admin privileges.
    """
    logger.info(f"Admin deleting listening test id={test_id}")
    await ListeningService.delete_test(test_id, t=t)


@router.get(
    "/parts/{part_id}",
    response_model=ListeningPartSerializer,
    summary="Get listening part",
)
async def get_listening_part(
    part_id: int,
    user=Depends(active_user),
    t: dict = Depends(get_translation),
    _: Any = Depends(audit_action("get_listening_part")),
):
    """
    Retrieve a listening part by its ID.
    """
    logger.info(f"Retrieving listening part id={part_id} for user {user.id}")
    part = await ListeningService.get_part(part_id, t=t)
    return await ListeningPartSerializer.from_orm(part)


@router.post(
    "/parts",
    response_model=ListeningPartSerializer,
    status_code=status.HTTP_201_CREATED,
    summary="Create listening part",
)
async def create_listening_part(
    listening_id: int = Form(...),
    part_number: int = Form(...),
    audio_file: UploadFile = File(...),
    _: Any = Depends(admin_required),
    t: dict = Depends(get_translation),
    __: Any = Depends(audit_action("create_listening_part")),
):
    """
    Create a new listening part. Requires admin privileges.
    """
    logger.info("Admin creating a new listening part")
    part = await ListeningService.create_part(
        listening_id=listening_id,
        part_number=part_number,
        audio_file=audio_file,
        t=t,
    )
    return await ListeningPartSerializer.from_orm(part)


@router.get(
    "/sections",
    response_model=List[ListeningSectionSerializer],
    summary="List all sections",
)
async def list_listening_sections(
    user=Depends(active_user),
    t: dict = Depends(get_translation),
    _: Any = Depends(audit_action("list_listening_sections")),
):
    """
    Retrieve all listening sections with their questions.
    """
    logger.info(f"Retrieving all listening sections for user {user.id}")
    sections = await ListeningService.list_sections()
    return await asyncio.gather(*[ListeningSectionSerializer.from_orm(sec) for sec in sections])


@router.get(
    "/sections/{section_id}",
    response_model=ListeningSectionSerializer,
    summary="Get listening section",
)
async def get_listening_section(
    section_id: int,
    user=Depends(active_user),
    t: dict = Depends(get_translation),
    _: Any = Depends(audit_action("get_listening_section")),
):
    """
    Retrieve a listening section by its ID.
    """
    logger.info(f"Retrieving listening section id={section_id} for user {user.id}")
    section = await ListeningService.get_section(section_id, t=t)
    return await ListeningSectionSerializer.from_orm(section)


@router.post(
    "/sections",
    response_model=ListeningSectionSerializer,
    status_code=status.HTTP_201_CREATED,
    summary="Create listening section",
)
async def create_listening_section(
    payload: ListeningSectionCreateSerializer,
    _: Any = Depends(admin_required),
    t: dict = Depends(get_translation),
    __: Any = Depends(audit_action("create_listening_section")),
):
    """
    Create a new listening section. Requires admin privileges.
    """
    logger.info("Admin creating a new listening section")
    section = await ListeningService.create_section(payload.dict())
    return await ListeningSectionSerializer.from_orm(section)


@router.delete(
    "/sections/{section_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete listening section",
)
async def delete_listening_section(
    section_id: int,
    _: Any = Depends(admin_required),
    t: dict = Depends(get_translation),
    __: Any = Depends(audit_action("delete_listening_section")),
):
    """
    Delete a listening section by its ID. Requires admin privileges.
    """
    logger.info(f"Admin deleting listening section id={section_id}")
    await ListeningService.delete_section(section_id, t=t)


@router.get(
    "/questions",
    response_model=List[ListeningQuestionSerializer],
    summary="List all questions",
)
async def list_listening_questions(
    user=Depends(active_user),
    t: dict = Depends(get_translation),
    _: Any = Depends(audit_action("list_listening_questions")),
):
    """
    Retrieve all listening questions.
    """
    logger.info(f"Retrieving all listening questions for user {user.id}")
    questions = await ListeningService.list_questions()
    return await asyncio.gather(*[ListeningQuestionSerializer.from_orm(q) for q in questions])


@router.get(
    "/questions/{question_id}",
    response_model=ListeningQuestionSerializer,
    summary="Get listening question",
)
async def get_listening_question(
    question_id: int,
    user=Depends(active_user),
    t: dict = Depends(get_translation),
    _: Any = Depends(audit_action("get_listening_question")),
):
    """
    Retrieve a listening question by its ID.
    """
    logger.info(f"Retrieving listening question id={question_id} for user {user.id}")
    question = await ListeningService.get_question(question_id, t=t)
    return await ListeningQuestionSerializer.from_orm(question)


@router.post(
    "/questions",
    response_model=ListeningQuestionSerializer,
    status_code=status.HTTP_201_CREATED,
    summary="Create listening question",
)
async def create_listening_question(
    payload: ListeningQuestionCreateSerializer,
    _: Any = Depends(admin_required),
    t: dict = Depends(get_translation),
    __: Any = Depends(audit_action("create_listening_question")),
):
    """
    Create a new listening question. Requires admin privileges.
    """
    logger.info("Admin creating a new listening question")
    question = await ListeningService.create_question(payload.dict())
    return await ListeningQuestionSerializer.from_orm(question)


@router.delete(
    "/questions/{question_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete listening question",
)
async def delete_listening_question(
    question_id: int,
    _: Any = Depends(admin_required),
    t: dict = Depends(get_translation),
    __: Any = Depends(audit_action("delete_listening_question")),
):
    """
    Delete a listening question by its ID. Requires admin privileges.
    """
    logger.info(f"Admin deleting listening question id={question_id}")
    await ListeningService.delete_question(question_id, t=t)


@router.post(
    "/session",
    response_model=UserListeningSessionSerializer,
    status_code=status.HTTP_201_CREATED,
    summary="Start a new listening session",
)
async def start_listening_session(
    request: Request,
    user=Depends(active_user),
    t: dict = Depends(get_translation),
    _: Any = Depends(audit_action("start_listening_session")),
):
    """
    Start a new listening session for the current user. Deducts tokens if available.
    """
    logger.info(f"User {user.id} is starting a new listening session")
    session = await ListeningService.start_session(user, request, t=t)
    return await UserListeningSessionSerializer.from_orm(session)


@router.get(
    "/session/{session_id}",
    response_model=UserListeningSessionSerializer,
    summary="Get session details",
)
async def get_listening_session(
    session_id: int,
    user=Depends(active_user),
    t: dict = Depends(get_translation),
    _: Any = Depends(audit_action("get_listening_session")),
):
    """
    Retrieve details of a specific listening session for the user.
    """
    logger.info(f"Retrieving session details for session_id={session_id}, user_id={user.id}")
    session = await ListeningService.get_session(session_id, user.id, t=t)
    return await UserListeningSessionSerializer.from_orm(session)


@router.post(
    "/session/{session_id}/cancel",
    status_code=status.HTTP_200_OK,
    summary="Cancel listening session",
)
async def cancel_listening_session(
    session_id: int,
    user=Depends(active_user),
    t: dict = Depends(get_translation),
    _: Any = Depends(audit_action("cancel_listening_session")),
):
    """
    Cancel an ongoing listening session if it is not already completed.
    """
    logger.info(f"User {user.id} requested cancellation of session_id={session_id}")
    await ListeningService.cancel_session(session_id, user.id, t=t)
    return {"detail": t["session_cancelled"]}


@router.get(
    "/session/{session_id}/data",
    response_model=ListeningDataSlimSerializer,  # <<< swapped to slim version
    summary="Get session data",
)
async def get_listening_data(
    session_id: int,
    user=Depends(active_user),
    t: dict = Depends(get_translation),
    _: Any = Depends(audit_action("get_listening_data")),
):
    """
    Retrieve all data required for a listening session, but only send back the fields that the frontend expects.
    """
    logger.info(f"Retrieving session data for session_id={session_id}, user_id={user.id}")
    data_dict = await ListeningService.get_session_data(session_id, user.id, t=t)

    # Build a “slim” parts array matching front’s IListeningData:
    slim_parts = []
    for part in data_dict["parts"]:
        slim_parts.append({
            "id": part["id"],
            "part_number": part["part_number"],
            "audio_file": part["audio_file"],
        })

    return {
        "session_id": data_dict["session_id"],
        "start_time": data_dict["start_time"],
        "status": data_dict["status"],
        "exam": data_dict["exam"],
        "parts": slim_parts,
    }


@router.post(
    "/session/{session_id}/submit",
    status_code=status.HTTP_200_OK,
    summary="Submit answers for session",
)
async def submit_listening_answers(
    session_id: int,
    payload: ListeningAnswerSerializer,
    user=Depends(active_user),
    t: dict = Depends(get_translation),
    _: Any = Depends(audit_action("submit_listening_answers")),
):
    """
    Submit answers for a listening session. Calculates scores and marks session completed.
    Frontend must send 'answers' keyed by numeric section_id.
    """
    logger.info(f"User {user.id} submitting answers for session_id={session_id}")
    await ListeningService.submit_answers(session_id, user.id, payload.dict(), t=t)
    return {"detail": t.get("answers_submitted", "Answers submitted successfully")}


@router.get(
    "/session/{session_id}/analyse",
    response_model=ListeningAnalyseResponseSerializer,
    summary="Get session analysis",
)
async def get_listening_analysis(
    session_id: int,
    user=Depends(active_user),
    t: dict = Depends(get_translation),
    _: Any = Depends(audit_action("get_listening_analysis")),
):
    """
    Retrieve analysis results for a completed listening session.
    """
    logger.info(f"Retrieving analysis for session_id={session_id}, user_id={user.id}")
    result = await ListeningService.get_analysis(session_id, user.id, t=t)

    # Build a payload that exactly matches IListeningAnalyse:
    analyse_dict = result["analyse"]
    # drop “feedback” if present, because IListeningAnalyse only expects correct_answers, overall_score, timing:
    slim_analyse = {
        "correct_answers": analyse_dict.get("correct_answers"),
        "overall_score": analyse_dict.get("overall_score"),
        "timing": analyse_dict.get("timing"),
    }
    # keep responses but drop any extra keys not in TS type
    slim_responses = []
    for r in result["responses"]:
        slim_responses.append({
            "id": r["id"],
            "user_answer": r["user_answer"],
            "is_correct": r["is_correct"],
            "score": r["score"],
            "correct_answer": r["correct_answer"],
            "question_index": r["question_index"],
        })

    return {
        "session_id": result["session_id"],
        "analyse": slim_analyse,
        "responses": slim_responses,
    }
