from pydantic import BaseModel
from typing import Optional


class CommentSerializer(BaseModel):
    id: int
    text: str
    user_id: int
    rate: float
    status: str

    class Config:
        from_attributes = True


class CommentCreateSerializer(BaseModel):
    text: str
    rate: float

    class Config:
        from_attributes = True


class CommentListSerializer(BaseModel):
    id: int
    text: str
    user: dict
    rate: float
    status: str

    class Config:
        from_attributes = True