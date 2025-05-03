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


class SpeakingQuestionSerializer(BaseModel):
    id: int
    speaking_id: int
    part: str
    title: Optional[str]
    content: str

    class Config:
        from_attributes = True


class SpeakingAnswerSerializer(BaseModel):
    id: int
    question_id: int
    text_answer: Optional[str]
    audio_answer: Optional[str]

    class Config:
        from_attributes = True