from pydantic import BaseModel
from typing import Optional

class ListeningSerializer(BaseModel):
    id: int
    status: str
    user_id: int
    start_time: Optional[str]
    end_time: Optional[str]

    class Config:
        from_attributes = True


class ListeningPart1Serializer(BaseModel):
    id: int
    listening_id: int
    content: str
    answer: Optional[str]
    audio: Optional[str]

    class Config:
        from_attributes = True


class ListeningPart2Serializer(BaseModel):
    id: int
    listening_id: int
    content: str
    answer: Optional[str]
    audio: Optional[str]

    class Config:
        from_attributes = True


class ListeningPart3Serializer(BaseModel):
    id: int
    listening_id: int
    content: str
    answer: Optional[str]
    audio: Optional[str]

    class Config:
        from_attributes = True