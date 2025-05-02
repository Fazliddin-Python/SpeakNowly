from pydantic import BaseModel
from typing import Optional

class ReadingSerializer(BaseModel):
    id: int
    status: str
    user_id: int
    start_time: Optional[str]
    end_time: Optional[str]

    class Config:
        from_attributes = True


class ReadingPart1Serializer(BaseModel):
    id: int
    reading_id: int
    content: str
    answer: Optional[str]

    class Config:
        from_attributes = True


class ReadingPart2Serializer(BaseModel):
    id: int
    reading_id: int
    content: str
    answer: Optional[str]

    class Config:
        from_attributes = True


class ReadingPart3Serializer(BaseModel):
    id: int
    reading_id: int
    content: str
    answer: Optional[str]

    class Config:
        from_attributes = True