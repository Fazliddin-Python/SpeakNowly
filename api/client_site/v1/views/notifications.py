from fastapi import APIRouter, HTTPException
from models.notifications import Message, ReadStatus, Comment
from api.client_site.v1.serializers.notifications import MessageSerializer, ReadStatusSerializer, CommentSerializer

router = APIRouter()

@router.get("/messages/", response_model=list[MessageSerializer])
async def get_messages():
    messages = await Message.all()
    return messages

@router.get("/messages/{message_id}/", response_model=MessageSerializer)
async def get_message(message_id: int):
    message = await Message.get_or_none(id=message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    return message

@router.get("/read-statuses/", response_model=list[ReadStatusSerializer])
async def get_read_statuses():
    statuses = await ReadStatus.all()
    return statuses

@router.get("/comments/", response_model=list[CommentSerializer])
async def get_comments():
    comments = await Comment.all()
    return comments