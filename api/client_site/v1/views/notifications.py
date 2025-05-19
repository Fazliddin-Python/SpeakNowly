import logging
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List
from tortoise.exceptions import DoesNotExist

from models.notifications import Message, ReadStatus
from ..serializers.notifications import (
    MessageSerializer,
    MessageListSerializer,
    ReadStatusSerializer,
)
from tasks.notifications_tasks import send_mass_notification

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/", response_model=List[MessageListSerializer])
async def get_notifications(
    user_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1),
):
    """
    Get a paginated list of notifications for a user.
    """
    logger.info("User %s requested notifications page=%s", user_id, page)
    offset = (page - 1) * page_size
    messages = await Message.filter(user_id=user_id).offset(offset).limit(page_size).all()
    if not messages:
        logger.warning("No notifications found for user %s", user_id)
        raise HTTPException(status_code=404, detail="No notifications found")
    
    # Add `is_read` status for each message
    result = []
    for message in messages:
        is_read = await ReadStatus.filter(message_id=message.id, user_id=user_id).exists()
        result.append({
            "id": message.id,
            "title": message.title,
            "description": message.description,
            "created_at": message.created_at,
            "is_read": is_read,
        })
    return result


@router.get("/{id}/", response_model=MessageSerializer)
async def get_notification(id: int, user_id: int):
    """
    Get a single notification by ID.
    """
    try:
        message = await Message.get(id=id, user_id=user_id)
        # Mark the notification as read
        await ReadStatus.get_or_create(message_id=id, user_id=user_id, defaults={"read_at": None})
        return message
    except DoesNotExist:
        raise HTTPException(status_code=404, detail="Notification not found")


@router.post("/{id}/mark-as-read/", response_model=ReadStatusSerializer)
async def mark_notification_as_read(id: int, user_id: int):
    """
    Mark a notification as read.
    """
    try:
        message = await Message.get(id=id, user_id=user_id)
        read_status, created = await ReadStatus.get_or_create(
            message_id=message.id,
            user_id=user_id,
            defaults={"read_at": None},
        )
        if not created:
            read_status.read_at = None
            await read_status.save()
        return read_status
    except DoesNotExist:
        raise HTTPException(status_code=404, detail="Notification not found")


@router.delete("/{id}/", status_code=204)
async def delete_notification(id: int, user_id: int):
    """
    Delete a notification by ID.
    """
    deleted_count = await Message.filter(id=id, user_id=user_id).delete()
    if not deleted_count:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"message": "Notification deleted successfully"}

@router.post("/mass-send/")
async def mass_send_notification_endpoint(user_ids: List[int], title: str, content: str):
    send_mass_notification.delay(user_ids, title, content)
    logger.info("Mass notification task started for %d users", len(user_ids))
    return {"message": "Notifications are being sent"}
