from fastapi import APIRouter, Query, Depends, Request, HTTPException, status
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from models.tests import Reading, UserListeningSession, Speaking, Writing
from models.analyses import ListeningAnalyse, ReadingAnalyse, SpeakingAnalyse, WritingAnalyse
from ...serializers.tests.history import HistoryItem, UserProgressSerializer, MainStatsSerializer
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


def _calc_duration(obj) -> Optional[int]:
    """
    Calculates duration in minutes between start_time and end_time.
    """
    if getattr(obj, "start_time", None) and getattr(obj, "end_time", None):
        return int((obj.end_time - obj.start_time).total_seconds() // 60)
    return None


@router.get(
    "/history/",
    response_model=List[HistoryItem],
    summary="Get user test history",
)
async def get_user_test_history(
    type: Optional[str] = Query(None, regex="^(listening|reading|speaking|writing)$"),
    show: Optional[str] = Query(None),
    user=Depends(active_user),
    t: dict = Depends(get_translation),
    _: Any = Depends(audit_action("get_user_test_history")),
):
    """
    Returns the user's test history (listening, reading, speaking, writing)
    with type, score, creation time, and duration.
    """
    user_id = user.id
    result = []

    # Reading
    if type in [None, "reading"]:
        readings = await Reading.filter(user_id=user_id).order_by("-created_at").all()
        for r in readings:
            passages = await r.passages.all()
            if not passages:
                continue
            passage_id = passages[0].id
            analyse = await ReadingAnalyse.filter(passage_id=passage_id, user_id=user_id).first()
            score = float(analyse.overall_score) if analyse else 0
            duration = _calc_duration(r)
            result.append({
                "type": "Reading",
                "score": score,
                "created_at": r.created_at,
                "duration": duration,
            })

    # Listening
    if type in [None, "listening"]:
        listenings = await UserListeningSession.filter(user_id=user_id).order_by("-created_at").all()
        for l in listenings:
            analyse = await ListeningAnalyse.get_or_none(session_id=l.id)
            score = float(analyse.overall_score) if analyse else 0
            duration = _calc_duration(l)
            result.append({
                "type": "Listening",
                "score": score,
                "created_at": l.created_at,
                "duration": duration,
            })

    # Speaking
    if type in [None, "speaking"]:
        speakings = await Speaking.filter(user_id=user_id).order_by("-created_at").all()
        for s in speakings:
            analyse = await SpeakingAnalyse.get_or_none(speaking_id=s.id)
            score = float(analyse.overall_band_score) if analyse else 0
            duration = _calc_duration(s)
            result.append({
                "type": "Speaking",
                "score": score,
                "created_at": s.created_at,
                "duration": duration,
            })

    # Writing
    if type in [None, "writing"]:
        writings = await Writing.filter(user_id=user_id).order_by("-created_at").all()
        for w in writings:
            analyse = await WritingAnalyse.get_or_none(writing_id=w.id)
            score = float(analyse.overall_band_score) if analyse else 0
            duration = _calc_duration(w)
            result.append({
                "type": "Writing",
                "score": score,
                "created_at": w.created_at,
                "duration": duration,
            })

    # Sorting and show=last
    result.sort(key=lambda x: x["created_at"], reverse=True)
    if show == "last":
        result = result[:5]

    return result


@router.get(
    "/progress/",
    response_model=UserProgressSerializer,
    summary="Get user progress"
)
async def get_user_progress(
    user=Depends(active_user),
    t: dict = Depends(get_translation),
):
    """
    Returns user progress: latest scores for each test type and the highest score.
    """
    user_id = user.id

    # Listening: последний анализ по последней сессии
    latest_listening = await ListeningAnalyse.filter(session__user_id=user_id).order_by("-session__start_time").first()
    listening_score = latest_listening.overall_score if latest_listening else None

    # Speaking: последний анализ по последнему Speaking
    latest_speaking = await SpeakingAnalyse.filter(speaking__user_id=user_id).order_by("-speaking__start_time").first()
    speaking_score = latest_speaking.overall_band_score if latest_speaking else None

    # Writing: последний анализ по последнему Writing
    latest_writing = await WritingAnalyse.filter(writing__user_id=user_id).order_by("-writing__start_time").first()
    writing_score = latest_writing.overall_band_score if latest_writing else None

    # Reading: последний Reading (score хранится в Reading)
    latest_reading = await Reading.filter(user_id=user_id).order_by("-start_time").first()
    reading_score = latest_reading.score if latest_reading else None

    latest = {
        "listening": listening_score,
        "speaking": speaking_score,
        "writing": writing_score,
        "reading": reading_score,
    }

    # Высший балл среди всех последних анализов (только не None)
    all_scores = [v for v in latest.values() if v is not None]
    highest = max(all_scores) if all_scores else 0

    return {"latest_analysis": latest, "highest_score": highest}


@router.get(
    "/progress/main-stats/",
    response_model=MainStatsSerializer,
    summary="Get main stats for user"
)
async def get_main_stats(
    user=Depends(active_user),
    t: dict = Depends(get_translation),
    _: Any = Depends(audit_action("get_main_stats")),
):
    """
    Returns the user's highest scores for each test type (stars).
    """
    user_id = user.id

    async def get_max_score(analyse_model, filter_key, score_key):
        analyses = await analyse_model.filter(**{filter_key + "__isnull": False}).all()
        scores = [float(getattr(a, score_key, 0)) for a in analyses if getattr(a, score_key, None) is not None]
        return int(max(scores)) if scores else 0

    return {
        "reading": await get_max_score(ReadingAnalyse, "user_id", "overall_score"),
        "speaking": await get_max_score(SpeakingAnalyse, "speaking_id", "overall_band_score"),
        "writing": await get_max_score(WritingAnalyse, "writing_id", "overall_band_score"),
        "listening": await get_max_score(ListeningAnalyse, "user_id", "overall_score"),
    }
