from pydantic import BaseModel
from typing import Optional

class GrammarSerializer(BaseModel):
    id: int
    status: str
    user_id: int
    start_time: Optional[str]
    end_time: Optional[str]

    class Config:
        from_attributes = True


class GrammarPart1Serializer(BaseModel):
    id: int
    grammar_id: int
    content: str
    answer: Optional[str]

    class Config:
        from_attributes = True


class GrammarPart2Serializer(BaseModel):
    id: int
    grammar_id: int
    content: str
    answer: Optional[str]

    class Config:
        from_attributes = True


class GrammarPart3Serializer(BaseModel):
    id: int
    grammar_id: int
    content: str
    answer: Optional[str]

    class Config:
        from_attributes = True