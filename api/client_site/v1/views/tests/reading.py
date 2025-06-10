import logging
from typing import Any, List, Dict

from fastapi import APIRouter, Depends, HTTPException, status, Query

from utils.auth.auth import get_current_user
from utils.i18n import get_translation
from utils.check_tokens import check_user_tokens
from tasks.analyses.reading_tasks import analyse_reading_task

from models import ReadingAnalyse, Reading
from models.transactions import TransactionType

from services.tests.reading_service import ReadingService
from services.analyses.reading_analyse_service import ReadingAnalyseService

from ...serializers.tests.reading import (
    StartReadingSerializer,
    PassageSerializer,
    PassageCreateSerializer,
    QuestionCreateSerializer,
    QuestionListSerializer,
    SubmitPassageAnswerSerializer,
    ReadingSerializer,
    ReadingAnalyseResponseSerializer
)

logger = logging.getLogger(__name__)
router = APIRouter()

# ========================
# Common Dependencies
# ========================
def audit_action(action: str):
    def wrapper(user=Depends(get_current_user)):
        logger.info(f"User {user.id} action='{action}'")
        return user
    return wrapper

def active_user(user=Depends(get_current_user), t=Depends(get_translation)):
    if not user.is_active:
        logger.warning(f"Inactive user {user.id} tried to access")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=t["inactive_user"])
    return user

def admin_required(user=Depends(get_current_user), t=Depends(get_translation)):
    if not (user.is_staff and user.is_superuser):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=t["permission_denied"])
    return user

# ========================
# Passage (Admin)
# ========================
@router.get("/passages/", response_model=List[PassageSerializer], summary="List all passages")
async def list_passages(
    t=Depends(get_translation),
    _: Any = Depends(admin_required),
    __: Any = Depends(audit_action("list_passages")),
):
    passages = await ReadingService.list_passages(t=t)
    return [await PassageSerializer.from_orm(p) for p in passages]

@router.post("/passages/", response_model=PassageSerializer, status_code=201, summary="Create passage")
async def create_passage(
    payload: PassageCreateSerializer,
    t: Dict[str, str] = Depends(get_translation),
    _: Any = Depends(admin_required),
    __: Any = Depends(audit_action("create_passage")),
):
    passage = await ReadingService.create_passage(payload.dict(), t=t)
    return await PassageSerializer.from_orm(passage)

@router.get("/passages/{passage_id}/", response_model=PassageSerializer, summary="Get passage by ID")
async def get_passage(
    passage_id: int,
    t: Dict[str, str] = Depends(get_translation),
    _: Any = Depends(admin_required)
):
    passage = await ReadingService.get_passage(passage_id, t=t)
    return await PassageSerializer.from_orm(passage)

@router.put("/passages/{passage_id}/", response_model=PassageSerializer, summary="Update passage")
async def update_passage(
    passage_id: int,
    payload: PassageCreateSerializer,
    t: Dict[str, str] = Depends(get_translation),
    _: Any = Depends(admin_required)
):
    passage = await ReadingService.update_passage(passage_id, payload.dict(), t=t)
    return await PassageSerializer.from_orm(passage)

@router.delete("/passages/{passage_id}/", status_code=204, summary="Delete passage")
async def delete_passage(
    passage_id: int,
    t: Dict[str, str] = Depends(get_translation),
    _: Any = Depends(admin_required)
):
    await ReadingService.delete_passage(passage_id, t=t)

# ========================
# Question (Admin)
# ========================

@router.get("/questions/", response_model=List[QuestionListSerializer], summary="List questions")
async def list_questions(
    t: Dict[str, str] = Depends(get_translation),
    _: Any = Depends(admin_required),
):
    questions = await ReadingService.list_questions(t=t)
    return [await QuestionListSerializer.from_orm(q) for q in questions]

@router.post("/questions/", response_model=QuestionListSerializer, status_code=201, summary="Create question")
async def create_question(
    payload: QuestionCreateSerializer,
    t: Dict[str, str] = Depends(get_translation),
    _: Any = Depends(admin_required)
):
    question = await ReadingService.create_question(payload.dict(), t=t)
    return await QuestionListSerializer.from_orm(question)

@router.get("/questions/{question_id}/", response_model=QuestionListSerializer, summary="Get question by ID")
async def get_question(
    question_id: int,
    t: Dict[str, str] = Depends(get_translation),
    _: Any = Depends(admin_required)
):
    question = await ReadingService.get_question(question_id, t=t)
    return await QuestionListSerializer.from_orm(question)

@router.put("/questions/{question_id}/", response_model=QuestionListSerializer, summary="Update question")
async def update_question(
    question_id: int,
    payload: QuestionCreateSerializer,
    t: Dict[str, str] = Depends(get_translation),
    _: Any = Depends(admin_required)
):
    question = await ReadingService.update_question(question_id, payload.dict(), t=t)
    return await QuestionListSerializer.from_orm(question)

@router.delete("/questions/{question_id}/", status_code=204, summary="Delete question")
async def delete_question(
    question_id: int,
    t: Dict[str, str] = Depends(get_translation),
    _: Any = Depends(admin_required)
):
    await ReadingService.delete_question(question_id, t=t)

# ========================
# Reading Session (User)
# ========================

@router.post("/start/", response_model=Dict[str, Any], summary="Start reading session")
async def start_reading(
    user=Depends(active_user),
    t=Depends(get_translation)
):
    await check_user_tokens(user, TransactionType.TEST_READING, None, t)
    reading, passages = await ReadingService.start_reading(user.id)
    if not reading or not passages:
        raise HTTPException(status_code=500, detail=t["internal_error"])

    # Build list of passages with questions
    result_passages = []
    for passage in passages:
        questions = await passage.questions.all().prefetch_related("variants")
        serialized_questions = [await QuestionListSerializer.from_orm(q) for q in questions]
        serialized_passage = await PassageSerializer.from_orm(passage)
        # attach questions
        serialized_passage_dict = serialized_passage.dict()
        serialized_passage_dict["questions"] = [q.dict() for q in serialized_questions]
        result_passages.append(serialized_passage_dict)

    return {
        "session_id": reading.id,
        "status": reading.status,
        "user_id": reading.user_id,
        "start_time": reading.start_time,
        "end_time": reading.end_time,
        "score": reading.score,
        "duration": reading.duration,
        "passages": result_passages,
    }

@router.post(
    "/{session_id}/submit/",
    response_model=Dict[str, Any],
    summary="(Legacy) Submit answers for a passage in session"
)
async def submit_legacy(
    session_id: int,
    payload: SubmitPassageAnswerSerializer,
    user=Depends(get_current_user),
    t=Depends(get_translation),
):
    # УБРАТЬ эту проверку:
    # if payload.reading_id != session_id:
    #     raise HTTPException(
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #         detail=t.get("invalid_request", "Invalid request")
    #     )

    try:
        total_score, error = await ReadingService.submit_answers(
            session_id=session_id,
            user_id=user.id,
            passage_id=payload.passage_id,
            answers=payload.answers
        )
    except Exception:
        logger.exception("Unexpected error in legacy submit")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=t.get("internal_server_error", "Internal server error")
        )

    if error:
        detail = t.get(error, error)
        logger.warning(
            "Legacy submit error: session=%s, passage=%s, user=%s, code=%s",
            session_id, payload.passage_id, user.id, error
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )

    return {
        "message": t.get("answers_submitted", "Answers submitted successfully"),
        "total_score": total_score
    }

@router.post("/{session_id}/finish/", response_model=Dict[str, Any], summary="Finish reading session")
async def finish_reading(
    session_id: int,
    user=Depends(active_user),
    t=Depends(get_translation)
):
    result, code = await ReadingService.finish_reading(session_id, user.id)
    if code != 200:
        detail = result.get("error") or t['internal_error']
        raise HTTPException(status_code=code, detail=detail)
    return result

@router.post("/{session_id}/cancel/", summary="Cancel session")
async def cancel_reading(
    session_id: int,
    user=Depends(active_user),
    t=Depends(get_translation)
):
    ok = await ReadingService.cancel_reading(session_id, user.id)
    if not ok:
        raise HTTPException(status_code=404, detail=t['session_not_found'])
    return {"message": t['session_cancelled']}

@router.post("/{session_id}/restart/", response_model=Dict[str, Any], summary="Restart session")
async def restart_reading(
    session_id: int,
    user=Depends(active_user),
    t=Depends(get_translation)
):
    reading, error = await ReadingService.restart_reading(session_id, user.id)
    if error:
        raise HTTPException(status_code=400, detail=t.get(error, t['internal_error']))

    # Return all passages after restart
    passages = await reading.passages.all()
    result_passages = []
    for passage in passages:
        questions = await passage.questions.all().prefetch_related("variants")
        serialized_questions = [await QuestionListSerializer.from_orm(q) for q in questions]
        serialized_passage = await PassageSerializer.from_orm(passage)
        serialized_passage_dict = serialized_passage.dict()
        serialized_passage_dict["questions"] = [q.dict() for q in serialized_questions]
        result_passages.append(serialized_passage_dict)

    return {
        "session_id": reading.id,
        "status": reading.status,
        "user_id": reading.user_id,
        "start_time": reading.start_time,
        "end_time": reading.end_time,
        "score": reading.score,
        "duration": reading.duration,
        "passages": result_passages,
    }

@router.get("/{session_id}/analysis/", response_model=ReadingAnalyseResponseSerializer, summary="Get reading analysis")
async def analyse_reading(
    session_id: int,
    page: int = Query(1, ge=1),
    user=Depends(active_user),
    t=Depends(get_translation)
):
    reading = await Reading.get_or_none(id=session_id)
    if not reading:
        raise HTTPException(status_code=404, detail=t['session_not_found'])

    exists = await ReadingAnalyse.filter(
        passage_id__in=await reading.passages.all().values_list("id", flat=True),
        user_id=user.id
    ).exists()

    if not exists:
        analyse_reading_task.apply_async(args=[session_id, user.id], queue='analyses')
        raise HTTPException(status_code=202, detail=t['analysis_started'])

    return await ReadingAnalyseService.get_analysis(session_id, user.id)
