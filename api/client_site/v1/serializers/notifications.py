from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class MessageSerializer(BaseModel):
    """Serializer for detailed notification."""
    id: int
    user_id: Optional[int]
    type: str
    title: str
    description: Optional[str]
    content: str
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class MessageListSerializer(BaseModel):
    """Serializer for listing notifications."""
    id: int
    title: str
    description: Optional[str]
    created_at: datetime
    is_read: bool

    @staticmethod
    def compute_is_read(user_id: int, message_id: int) -> bool:
        """
        Logic to check if the message is read.
        Example: Query the database to check ReadStatus.
        """
        # Replace this with actual logic to check if the message is read
        return True  # Example: Always returns True

    class Config:
        from_attributes = True


class ReadStatusSerializer(BaseModel):
    """Serializer for read status of a notification."""
    id: int
    message_id: int
    user_id: int
    read_at: Optional[datetime]

    class Config:
        from_attributes = True