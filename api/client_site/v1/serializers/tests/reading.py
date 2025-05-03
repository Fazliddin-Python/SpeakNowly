from pydantic import BaseModel
from typing import Optional, List


class ReadingSerializer(BaseModel):
    id: int
    status: str
    user_id: int
    start_time: str
    end_time: Optional[str]
    score: float
    duration: int

    class Config:
        from_attributes = True


class PassageSerializer(BaseModel):
    id: int
    level: str
    number: int
    title: str
    text: str
    skills: List[str]

    class Config:
        from_attributes = True


class QuestionSerializer(BaseModel):
    id: int
    passage_id: int
    text: str
    type: str
    score: int
    correct_answer: str

    class Config:
        from_attributes = True


class VariantSerializer(BaseModel):
    id: int
    question_id: int
    text: str
    is_correct: bool

    class Config:
        from_attributes = True


class AnswerSerializer(BaseModel):
    id: int
    status: str
    user_id: int
    question_id: int
    variant_id: Optional[int]
    text: str
    explanation: Optional[str]
    is_correct: bool
    correct_answer: Optional[str]

    class Config:
        from_attributes = True