from typing import Optional, List
from ..base import BaseSerializer, SafeSerializer


class ReadingSerializer(SafeSerializer):
    """Serializer for reading tests (GET requests)."""
    status: str
    user_id: int
    start_time: str
    end_time: Optional[str]
    score: float
    duration: int


class PassageSerializer(SafeSerializer):
    """Serializer for passages in a reading test (GET requests)."""
    level: str
    number: int
    title: str
    text: str
    skills: List[str]


class QuestionSerializer(SafeSerializer):
    """Serializer for questions in a reading passage (GET requests)."""
    passage_id: int
    text: str
    type: str
    score: int
    correct_answer: str


class VariantSerializer(SafeSerializer):
    """Serializer for answer variants in a reading question (GET requests)."""
    question_id: int
    text: str
    is_correct: bool


class AnswerSerializer(BaseSerializer):
    """Serializer for user answers in a reading test (POST/PUT requests)."""
    status: str
    user_id: int
    question_id: int
    variant_id: Optional[int]
    text: str
    explanation: Optional[str]
    is_correct: bool
    correct_answer: Optional[str]