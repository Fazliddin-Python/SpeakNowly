from typing import Optional
from ..base import BaseSerializer, SafeSerializer


class SpeakingSerializer(SafeSerializer):
    """Serializer for speaking tests (GET requests)."""
    status: str
    user_id: int
    start_time: Optional[str]
    end_time: Optional[str]


class SpeakingQuestionSerializer(SafeSerializer):
    """Serializer for questions in a speaking test (GET requests)."""
    speaking_id: int
    part: str
    title: Optional[str]
    content: str


class SpeakingAnswerSerializer(BaseSerializer):
    """Serializer for user answers in a speaking test (POST/PUT requests)."""
    question_id: int
    text_answer: Optional[str]
    audio_answer: Optional[str]