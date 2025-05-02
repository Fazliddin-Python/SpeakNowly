from pydantic import BaseModel
from typing import Optional

class WritingSerializer(BaseModel):
    id: int
    status: str
    user_id: int
    start_time: Optional[str]
    end_time: Optional[str]

    class Config:
        from_attributes = True


class WritingPart1Serializer(BaseModel):
    id: int
    writing_id: int
    content: str
    answer: Optional[str]
    diagram: Optional[str]
    diagram_data: Optional[dict]

    class Config:
        from_attributes = True


class WritingPart2Serializer(BaseModel):
    id: int
    writing_id: int
    content: str
    answer: Optional[str]

    class Config:
        from_attributes = True