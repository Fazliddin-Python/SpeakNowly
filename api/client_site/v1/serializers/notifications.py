from pydantic import BaseModel
from typing import Optional

class MessageSerializer(BaseModel):
    id: int
    user_id: Optional[int]
    type: str
    title: str
    description: Optional[str]
    content: str

    class Config:
        from_attributes = True


class ReadStatusSerializer(BaseModel):
    id: int
    message_id: Optional[int]
    user_id: int
    read_at: Optional[str]

    class Config:
        from_attributes = True


class CommentSerializer(BaseModel):
    id: int
    user_id: int
    message_id: Optional[int]
    content: str
    created_at: str

    class Config:
        from_attributes = True