from typing import Optional, List
from ..base import BaseSerializer, SafeSerializer


class ListeningSerializer(SafeSerializer):
    """Serializer for listening tests (GET requests)."""
    title: str
    description: str


class ListeningPartSerializer(SafeSerializer):
    """Serializer for parts of a listening test (GET requests)."""
    listening_id: int
    part_number: int
    audio_file: str


class ListeningSectionSerializer(SafeSerializer):
    """Serializer for sections of a listening part (GET requests)."""
    part_id: int
    section_number: int
    start_index: int
    end_index: int
    question_type: str
    question_text: Optional[str]
    options: Optional[List[str]]


class ListeningQuestionSerializer(SafeSerializer):
    """Serializer for questions in a listening section (GET requests)."""
    section_id: int
    index: int
    options: Optional[List[str]]
    correct_answer: str


class UserListeningSessionSerializer(SafeSerializer):
    """Serializer for user listening sessions (GET requests)."""
    user_id: int
    exam_id: int
    status: str
    start_time: str
    end_time: Optional[str]


class UserResponseSerializer(BaseSerializer):
    """Serializer for user responses in listening tests (POST/PUT requests)."""
    session_id: int
    user_id: int
    question_id: int
    user_answer: str
    is_correct: bool
    score: int