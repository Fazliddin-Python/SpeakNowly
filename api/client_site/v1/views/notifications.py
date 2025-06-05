import logging
from fastapi import APIRouter, HTTPException, Depends, status, Request
from typing import List
from tortoise.exceptions import DoesNotExist

from models.notifications import Message, ReadStatus
from ..serializers.notifications import (
    MessageListSerializer,
    MessageDetailSerializer,
    MessageSerializer,
    ReadStatusSerializer,
)
from utils.i18n import get_translation
from utils.auth.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()

def _translate(obj, field: str, lang: str) -> str:
    """
    1) Try <field>_<lang>
    2) Fallback to <field>_en
    3) Fallback to empty string
    """
    return getattr(obj, f"{field}_{lang}", None) or getattr(obj, f"{field}_en", None) or ""

@router.get("/", response_model=List[MessageListSerializer])
async def list_notifications(
    request: Request,
    user=Depends(get_current_user),
    t: dict = Depends(get_translation),
):
    """
    List all notifications for the current user with translation support (no pagination).
    """
    raw_lang = request.headers.get("Accept-Language", "en").split(",")[0]
    lang = raw_lang.split("-")[0].lower()
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
    """
    Get notification detail and mark as read.
    """
    raw_lang = request.headers.get("Accept-Language", "en").split(",")[0]
    lang = raw_lang.split("-")[0].lower()
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

@router.post("/", response_model=MessageDetailSerializer, status_code=status.HTTP_201_CREATED)
async def create_notification(
    data: MessageSerializer,
    request: Request,
    user=Depends(get_current_user),
    t: dict = Depends(get_translation),
):
    """
    Create a new notification for the current user.
    """
    msg = await Message.create(
        user_id=user.id,
        type=data.type,
        title_en=data.title,
        description_en=data.description,
        content_en=data.content,
    )
    raw_lang = request.headers.get("Accept-Language", "en").split(",")[0]
    lang = raw_lang.split("-")[0].lower()
    return MessageDetailSerializer(
        id=msg.id,
        title=_translate(msg, "title", lang),
        description=_translate(msg, "description", lang),
        content=_translate(msg, "content", lang),
        created_at=msg.created_at
    )

@router.put("/{id}/", response_model=MessageDetailSerializer)
async def update_notification(
    id: int,
    data: MessageSerializer,
    request: Request,
    user=Depends(get_current_user),
    t: dict = Depends(get_translation),
):
    """
    Update an existing notification for the current user.
    """
    msg = await Message.get_or_none(id=id, user_id=user.id)
    if not msg:
        raise HTTPException(status_code=404, detail=t.get("notification_not_found", "Notification not found"))
    msg.type = data.type
    msg.title_en = data.title
    msg.description_en = data.description
    msg.content_en = data.content
    await msg.save()
    raw_lang = request.headers.get("Accept-Language", "en").split(",")[0]
    lang = raw_lang.split("-")[0].lower()
    return MessageDetailSerializer(
        id=msg.id,
        title=_translate(msg, "title", lang),
        description=_translate(msg, "description", lang),
        content=_translate(msg, "content", lang),
        created_at=msg.created_at
    )

@router.post("/{id}/mark-as-read/", response_model=ReadStatusSerializer)
async def mark_notification_as_read(
    id: int,
    user=Depends(get_current_user),
    t: dict = Depends(get_translation),
):
    """
    Mark a notification as read.
    """
    msg = await Message.get_or_none(id=id, user_id=user.id)
    if not msg:
        raise HTTPException(status_code=404, detail=t.get("notification_not_found", "Notification not found"))
    read_status, _ = await ReadStatus.get_or_create(
        message_id=msg.id,
        user_id=user.id,
        defaults={"read_at": None},
    )
    return read_status

@router.delete("/{id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_notification(
    id: int,
    user=Depends(get_current_user),
    t: dict = Depends(get_translation),
):
    """
    Delete a notification by ID.
    """
    deleted_count = await Message.filter(id=id, user_id=user.id).delete()
    if not deleted_count:
        raise HTTPException(status_code=404, detail=t.get("notification_not_found", "Notification not found"))
    return {"message": t.get("notification_deleted", "Notification deleted successfully")}
