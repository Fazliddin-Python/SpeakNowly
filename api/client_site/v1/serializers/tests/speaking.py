from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class QuestionPart(BaseModel):
    """
    Represents a single question part (part1, part2, or part3)
    as seen in the front-end TS interface.
    """
    id: int
    title: str
    content: str


class Questions(BaseModel):
    """
    Groups three QuestionPart objects under keys: part1, part2, part3.
    """
    part1: QuestionPart
    part2: QuestionPart
    part3: QuestionPart


class Analyse(BaseModel):
    """
    Represents the IELTS speaking analysis object, with all fields as strings
    to match the front-end TypeScript interface.
    """
    id: int
    speaking: int
    feedback: str
    overall_band_score: str
    fluency_and_coherence_score: str
    fluency_and_coherence_feedback: str
    lexical_resource_score: str
    lexical_resource_feedback: str
    grammatical_range_and_accuracy_score: str
    grammatical_range_and_accuracy_feedback: str
    pronunciation_score: str
    pronunciation_feedback: str


class SpeakingResponseType(BaseModel):
    """
    The top-level response model for a Speaking test, matching:
      export interface SpeakingResponseType { … }
    """
    id: int
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    status: str
    questions: Questions
    analyse: Optional[Analyse] = None
