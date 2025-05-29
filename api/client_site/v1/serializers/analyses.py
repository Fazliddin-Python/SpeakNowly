from typing import Optional, Any
from pydantic import BaseModel, Field
from datetime import timedelta
from .base import SafeSerializer, BaseModel

class ListeningAnalyseSerializer(BaseModel):
    """Serializer for listening session analysis results."""
    session_id: int
    user_id: Optional[int] = None
    correct_answers: int
    overall_score: float
    timing: Optional[Any] = None
    status: str
    feedback: Optional[Any] = None

class ReadingAnalyseSerializer(SafeSerializer):
    reading_id: int
    user_id: int
    correct_answers: int
    overall_score: float
    timing: str
    feedback: str

class SpeakingAnalyseSerializer(SafeSerializer):
    speaking_id: int
    feedback: Optional[str]
    overall_band_score: Optional[float]
    fluency_and_coherence_score: Optional[float]
    fluency_and_coherence_feedback: Optional[str]
    lexical_resource_score: Optional[float]
    lexical_resource_feedback: Optional[str]
    grammatical_range_and_accuracy_score: Optional[float]
    grammatical_range_and_accuracy_feedback: Optional[str]
    pronunciation_score: Optional[float]
    pronunciation_feedback: Optional[str]
    duration: Optional[str]

class WritingAnalyseSerializer(SafeSerializer):
    writing_id: int
    task_achievement_feedback: str
    task_achievement_score: float
    lexical_resource_feedback: str
    lexical_resource_score: float
    coherence_and_cohesion_feedback: str
    coherence_and_cohesion_score: float
    grammatical_range_and_accuracy_feedback: str
    grammatical_range_and_accuracy_score: float
    word_count_feedback: str
    word_count_score: float
    timing_feedback: str
    timing_time: Optional[str]
    overall_band_score: float
    total_feedback: str