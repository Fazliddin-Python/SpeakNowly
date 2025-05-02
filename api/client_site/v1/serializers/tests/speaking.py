from pydantic import BaseModel
from typing import Optional

class SpeakingSerializer(BaseModel):
    id: int
    status: str
    user_id: int
    start_time: Optional[str]
    end_time: Optional[str]

    class Config:
        from_attributes = True


class SpeakingPart1Serializer(BaseModel):
    id: int
    speaking_id: int
    content: str
    answer: Optional[str]
    audio: Optional[str]

    class Config:
        from_attributes = True


class SpeakingPart2Serializer(BaseModel):
    id: int
    speaking_id: int
    content: str
    answer: Optional[str]
    audio: Optional[str]

    class Config:
        from_attributes = True


class SpeakingPart3Serializer(BaseModel):
    id: int
    speaking_id: int
    content: str
    answer: Optional[str]
    audio: Optional[str]

    class Config:
        from_attributes = True