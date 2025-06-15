from fastapi import APIRouter, HTTPException, Depends, status, Request
from typing import List
from models.notifications import Message, ReadStatus
from ..serializers.notifications import MessageListSerializer, MessageDetailSerializer
from utils.auth import get_current_user
from utils.i18n import get_translation

router = APIRouter()

def _translate(obj, field: str, lang: str) -> str:
    """Get translated field or fallback."""
    return getattr(obj, f"{field}_{lang}", None) or getattr(obj, f"{field}_en", None) or getattr(obj, field, "") or ""

@router.get("/", response_model=List[MessageListSerializer])
async def list_notifications(
    request: Request,
    user=Depends(get_current_user),
    t: dict = Depends(get_translation),
):
    """List all notifications for current user."""
    lang = (request.headers.get("Accept-Language", "en").split(",")[0].split("-")[0]).lower()
    messages = await Message.filter(user_id=user.id).order_by("-created_at")
    result = []
    for msg in messages:
        title = _translate(msg, "title", lang)
        description = _translate(msg, "description", lang)
        is_read = await ReadStatus.filter(message_id=msg.id, user_id=user.id).exists()
        result.append(MessageListSerializer(
            id=msg.id,
            title=title,
            description=description,
            created_at=msg.created_at,
            is_read=is_read
        ))
    return result

@router.get("/{id}/", response_model=MessageDetailSerializer)
async def notification_detail(
    id: int,
    request: Request,
    user=Depends(get_current_user),
    t: dict = Depends(get_translation),
):
    """Get notification detail and mark as read."""
    lang = (request.headers.get("Accept-Language", "en").split(",")[0].split("-")[0]).lower()
    msg = await Message.get_or_none(id=id, user_id=user.id)
    if not msg:
        raise HTTPException(status_code=404, detail=t.get("notification_not_found", "Notification not found"))
    await ReadStatus.get_or_create(message_id=msg.id, user_id=user.id)
    return MessageDetailSerializer(
        id=msg.id,
        title=_translate(msg, "title", lang),
        description=_translate(msg, "description", lang),
        content=_translate(msg, "content", lang),
        created_at=msg.created_at
    )