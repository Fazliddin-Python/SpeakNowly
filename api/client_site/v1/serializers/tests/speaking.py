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
    Represents the IELTS speaking analysis object, with string fields
    to match the frontend interface.
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


class SpeakingCreate(BaseModel):
    """
    Request model for creating Speaking.
    Fields are optional, status is usually set by default on the server.
    """
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


class SpeakingAnalyseCreate(BaseModel):
    """
    Request model for creating/updating analysis (if a separate endpoint is needed).
    Fields are strings to match the frontend; the server can convert to Decimal when saving.
    """
    speaking: int
    feedback: Optional[str] = None
    overall_band_score: Optional[str] = None
    fluency_and_coherence_score: Optional[str] = None
    fluency_and_coherence_feedback: Optional[str] = None
    lexical_resource_score: Optional[str] = None
    lexical_resource_feedback: Optional[str] = None
    grammatical_range_and_accuracy_score: Optional[str] = None
    grammatical_range_and_accuracy_feedback: Optional[str] = None
    pronunciation_score: Optional[str] = None
    pronunciation_feedback: Optional[str] = None
    duration: Optional[str] = None  # for example, ISO 8601 duration if the frontend sends it


class SpeakingAudioAnswerResult(BaseModel):
    """
    Result after uploading audio: either a message or an analysis.
    """
    detail: Optional[str] = None
    analyse: Optional[Analyse] = None

