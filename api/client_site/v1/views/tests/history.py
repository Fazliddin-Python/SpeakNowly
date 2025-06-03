from fastapi import APIRouter, Depends, Query
from typing import List, Optional

from tortoise.exceptions import DoesNotExist

from models.tests import Reading, Speaking, Writing, UserListeningSession
from models import ReadingAnalyse, SpeakingAnalyse, WritingAnalyse, ListeningAnalyse

from ...serializers.tests.history import HistoryItem
from utils.auth.auth import get_current_user

router = APIRouter()

@router.get("/", response_model=List[HistoryItem])
async def get_history(
    type: Optional[str] = Query(None, description="reading|listening|speaking|writing"),
    show: Optional[str] = Query(None, description="if show='last', returns the last 5"),
    current_user=Depends(get_current_user),
):
    """
    Collects history for all types:
    - For Reading: uses ReadingAnalyse
    - For Listening: uses UserListeningSession + ListeningAnalyse
    - For Speaking: uses Speaking + SpeakingAnalyse
    - For Writing: uses Writing + WritingAnalyse

    Supports filtering by ?type=<type> and ?show=last
    """
    items = []

    # --- Reading ---
    # Get all ReadingAnalyse records for the current user
    reading_analyses = await ReadingAnalyse.filter(user_id=current_user.id).all()
    for ana in reading_analyses:
        # Assume BaseModel provides a created_at field
        created = getattr(ana, "created_at", None)
        if created is None:
            continue
        # Duration in minutes
        dur = int(ana.timing.total_seconds() // 60) if ana.timing else None

        items.append({
            "type": "reading",
            "score": float(ana.overall_score),
            "created_at": created,
            "duration": dur,
        })

    # --- Listening ---
    # Get all UserListeningSession records for the current user
    listening_sessions = await UserListeningSession.filter(user_id=current_user.id).all()
    for session in listening_sessions:
        created = getattr(session, "created_at", None)
        if created is None:
            continue
        # Duration = difference between end_time and start_time in minutes
        if session.start_time and session.end_time:
            dur = int((session.end_time - session.start_time).total_seconds() // 60)
        else:
            dur = None
        # Try to get the related analysis
        try:
            ana = await ListeningAnalyse.get(session_id=session.id)
            score = float(ana.overall_score)
        except DoesNotExist:
            score = 0.0

        items.append({
            "type": "listening",
            "score": score,
            "created_at": created,
            "duration": dur,
        })

    # --- Speaking ---
    # Get all Speaking objects where user=current_user
    speaking_objs = await Speaking.filter(user_id=current_user.id).all()
    for sp in speaking_objs:
        created = getattr(sp, "created_at", None)
        if created is None:
            continue
        # Duration = difference between end_time and start_time in minutes
        if getattr(sp, "start_time", None) and getattr(sp, "end_time", None):
            dur = int((sp.end_time - sp.start_time).total_seconds() // 60)
        else:
            dur = None
        # Try to get the related OneToOne analysis
        try:
            ana = await SpeakingAnalyse.get(speaking_id=sp.id)
            score = float(ana.overall_band_score) if ana.overall_band_score is not None else 0.0
        except DoesNotExist:
            score = 0.0

        items.append({
            "type": "speaking",
            "score": score,
            "created_at": created,
            "duration": dur,
        })

    # --- Writing ---
    # Get all Writing objects where user=current_user
    writing_objs = await Writing.filter(user_id=current_user.id).all()
    for wr in writing_objs:
        created = getattr(wr, "created_at", None)
        if created is None:
            continue
        # Duration = difference between end_time and start_time in minutes
        if getattr(wr, "start_time", None) and getattr(wr, "end_time", None):
            dur = int((wr.end_time - wr.start_time).total_seconds() // 60)
        else:
            dur = None
        # Try to get the related OneToOne analysis
        try:
            ana = await WritingAnalyse.get(writing_id=wr.id)
            score = float(ana.overall_band_score)
        except DoesNotExist:
            score = 0.0

        items.append({
            "type": "writing",
            "score": score,
            "created_at": created,
            "duration": dur,
        })

    # Sort all records by created_at descending
    items_sorted = sorted(items, key=lambda x: x["created_at"], reverse=True)

    # If ?type= is provided, filter by type (case-insensitive)
    if type:
        type_lower = type.lower()
        items_sorted = [it for it in items_sorted if it["type"].lower() == type_lower]

    # If show=last, take the first 5 elements
    if show == "last":
        items_sorted = items_sorted[:5]

    return items_sorted
