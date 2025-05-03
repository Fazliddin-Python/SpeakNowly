from pydantic import BaseModel
from typing import Optional


class MessageSerializer(BaseModel):
    id: int
    user_id: Optional[int]
    type: str
    title: str
    description: Optional[str]
    content: str
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class MessageListSerializer(BaseModel):
    id: int
    title: str
    description: Optional[str]
    created_at: str
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
    id: int
    message_id: int
    user_id: int
    read_at: Optional[str]

    class Config:
        from_attributes = True