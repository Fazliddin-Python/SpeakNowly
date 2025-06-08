from pydantic import Field
from typing import Optional
from datetime import datetime, timezone
from enum import Enum
from models.notifications import MessageType
from .base import SafeSerializer, BaseSerializer


class MessageSerializer(SafeSerializer):
    """Serializer for detailed notification."""
    user_id: Optional[int]
    type: MessageType
    title: str
    description: Optional[str]
    content: str


class MessageListSerializer(SafeSerializer):
    """Serializer for listing notifications."""
    title: str
    description: Optional[str]
    is_read: bool = Field(..., description="Whether the message is read")


class MessageDetailSerializer(SafeSerializer):
    title: str
    description: Optional[str]
    content: Optional[str]


class ReadStatusSerializer(SafeSerializer):
    """Serializer for read status of a notification."""
    message_id: int
    user_id: int
    read_at: Optional[datetime]