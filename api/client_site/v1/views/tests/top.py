from fastapi import APIRouter, Depends, Query
from typing import List, Optional
from datetime import datetime, timedelta

from models.users import User
from models.transactions import TokenTransaction
from ...serializers.tests.top import TopUserIELTSSerializer
from services.tests.ielts_score import IELTSScoreCalculator
from utils.auth.auth import get_current_user

router = APIRouter()

def active_user(user=Depends(get_current_user)):
    """
    Ensures the user is active.
    """
    if not user.is_active:
        from fastapi import HTTPException, status
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is not active")
    return user

@router.get(
    "/",
    response_model=List[TopUserIELTSSerializer],
    summary="Get real top users by IELTS score"
)
async def get_top_users(
    period: Optional[str] = Query(None, description="Filter by period: week, month, etc."),
    test_type: Optional[str] = Query(None, description="Filter by test type"),
    user=Depends(active_user),
):
    """
    Returns the top users by IELTS score (real data).
    """
    now = datetime.utcnow()
    if period == "week":
        start_date = now - timedelta(days=7)
    elif period == "month":
        start_date = now - timedelta(days=30)
    else:
        start_date = None

    transactions = await TokenTransaction.all()
    if start_date:
        transactions = [t for t in transactions if t.created_at >= start_date]
    if test_type:
        transactions = [t for t in transactions if t.transaction_type == test_type.upper()]

    # Get unique user_ids from transactions
    user_ids = list({t.user_id for t in transactions if t.user_id})

    # Get all users in one query
    users = await User.filter(id__in=user_ids)
    users_dict = {u.id: u for u in users}

    user_scores = {}
    for user_id in user_ids:
        user_obj = users_dict.get(user_id)
        if not user_obj:
            continue
        score = await IELTSScoreCalculator.calculate(user_obj)
        user_scores[user_obj.id] = {
            "first_name": user_obj.first_name or "",
            "last_name": user_obj.last_name or "",
            "ielts_score": score,
            "image": getattr(user_obj, "photo", None),
        }

    sorted_users = sorted(user_scores.values(), key=lambda x: x["ielts_score"], reverse=True)
    return sorted_users[:100]