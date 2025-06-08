from fastapi import APIRouter, Query, Depends, Request, HTTPException, status
from typing import List, Optional
from datetime import datetime
import logging

from models.tests import Reading, UserListeningSession, Speaking, Writing
from models.analyses import ListeningAnalyse, ReadingAnalyse, SpeakingAnalyse, WritingAnalyse
from ...serializers.tests.history import HistoryItem, UserProgressSerializer, MainStatsSerializer
from services.tests.user_progress_service import UserProgressService
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


# --- Helper to calculate duration in minutes ---
def _calc_duration(obj) -> Optional[int]:
    if getattr(obj, "start_time", None) and getattr(obj, "end_time", None):
        return int((obj.end_time - obj.start_time).total_seconds() // 60)
    return None

# --- History Endpoint ---
@router.get(
    "/history/", response_model=List[HistoryItem],
    summary="Get user test history",
)
async def get_user_test_history(
    type: Optional[str] = Query(None, regex="^(listening|reading|speaking|writing)$"),
    show: Optional[str] = Query(None),
    user=Depends(active_user),
    t: dict = Depends(get_translation),
    _: any = Depends(audit_action("get_user_test_history")),
):
    """
    Retrieve combined history of all test sessions for the authenticated user.
    Supports filtering by type and showing only last 5 records (show=last).
    """
    user_id = user.id

    # Load all sessions
    reading = await Reading.filter(user_id=user_id).all()
    listening = await UserListeningSession.filter(user_id=user_id).all()
    speaking = await Speaking.filter(user_id=user_id).all()
    writing = await Writing.filter(user_id=user_id).all()

    result = []

    # Append Reading
    if type in [None, "reading"]:
        for r in reading:
            passages = await r.passages.all()
            if not passages:
                continue
            passage_id = passages[0].id
            analyse = await ReadingAnalyse.get_or_none(passage_id=passage_id, user_id=user_id)
            if analyse:
                result.append({
                    "type": "Reading",
                    "score": float(analyse.overall_score),
                    "created_at": r.created_at,
                    "duration": _calc_duration(r),
                })

    # Append Listening
    if type in [None, "listening"]:
        for l in listening:
            analyse = await ListeningAnalyse.get_or_none(session_id=l.id)
            if analyse:
                duration = _calc_duration(l)
                result.append({
                    "type": "Listening",
                    "score": float(analyse.overall_score),
                    "created_at": l.created_at,
                    "duration": duration,
                })

    # Append Speaking
    if type in [None, "speaking"]:
        for s in speaking:
            analyse = await SpeakingAnalyse.get_or_none(speaking_id=s.id)
            if analyse:
                duration = _calc_duration(s)
                result.append({
                    "type": "Speaking",
                    "score": float(analyse.overall_band_score),
                    "created_at": s.created_at,
                    "duration": duration,
                })

    # Append Writing
    if type in [None, "writing"]:
        for w in writing:
            analyse = await WritingAnalyse.get_or_none(writing_id=w.id)
            if analyse:
                duration = _calc_duration(w)
                result.append({
                    "type": "Writing",
                    "score": float(analyse.overall_band_score),
                    "created_at": w.created_at,
                    "duration": duration,
                })

    # Sort and paginate
    result.sort(key=lambda x: x["created_at"], reverse=True)
    if show == "last":
        result = result[:5]

    return result

# --- User Progress Endpoint ---
@router.get(
    "/progress/", response_model=UserProgressSerializer,
    summary="Get user progress"
)
async def get_user_progress(
    user=Depends(active_user),
    t: dict = Depends(get_translation),
    _: any = Depends(audit_action("get_user_progress")),
):
    """
    Retrieve latest analysis and highest score for the authenticated user.
    """
    latest = await UserProgressService.get_latest_analysis(user.id)
    highest = await UserProgressService.get_highest_score(user.id)
    return {"latest_analysis": latest, "highest_score": highest}

# --- Main Stats Endpoint ---
@router.get(
    "/progress/main-stats/", response_model=MainStatsSerializer,
    summary="Get main stats for user"
)
async def get_main_stats(
    user=Depends(active_user),
    t: dict = Depends(get_translation),
    _: any = Depends(audit_action("get_main_stats")),
):
    """
    Retrieve individual latest scores across all test types for the authenticated user.
    """
    user_id = user.id

    # Get last Speaking score
    last_s = await Speaking.filter(user_id=user_id).order_by("-start_time").first()
    sp_an = await SpeakingAnalyse.get_or_none(speaking_id=last_s.id) if last_s else None
    speaking_score = sp_an.overall_band_score if sp_an else 0

    # Get last Reading score
    last_r = await Reading.filter(user_id=user_id).order_by("-start_time").first()
    reading_score = last_r.score if last_r else 0

    # Get last Writing score
    last_w = await Writing.filter(user_id=user_id).order_by("-start_time").first()
    w_an = await WritingAnalyse.get_or_none(writing_id=last_w.id) if last_w else None
    writing_score = w_an.overall_band_score if w_an else 0

    # Get last Listening score
    la = await ListeningAnalyse.filter(user_id=user_id).order_by("-created_at").first()
    listening_score = la.overall_score if la else 0

    return {
        "reading": reading_score,
        "speaking": speaking_score,
        "writing": writing_score,
        "listening": listening_score,
    }
