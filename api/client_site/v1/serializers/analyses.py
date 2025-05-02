from pydantic import BaseModel
from typing import Optional

class ListeningAnalyseSerializer(BaseModel):
    id: int
    listening_id: int
    correct_answers: int
    overall_score: float
    timing: str
    feedback: str

    class Config:
        from_attributes = True


class WritingAnalyseSerializer(BaseModel):
    id: int
    writing_id: int
    overall_band_score: float
    total_feedback: str

    class Config:
        from_attributes = True


class SpeakingAnalyseSerializer(BaseModel):
    id: int
    speaking_id: int
    overall_band_score: float
    total_feedback: str

    class Config:
        from_attributes = True


class ReadingAnalyseSerializer(BaseModel):
    id: int
    reading_id: int
    correct_answers: int
    overall_score: float
    feedback: str

    class Config:
        from_attributes = True


class GrammarAnalyseSerializer(BaseModel):
    id: int
    grammar_id: int
    correct_answers: int
    overall_score: float
    feedback: str

    class Config:
        from_attributes = True
