from typing import Optional
from ..base import BaseSerializer, SafeSerializer


class WritingSerializer(SafeSerializer):
    """Serializer for writing tests (GET requests)."""
    status: str
    user_id: int
    start_time: Optional[str]
    end_time: Optional[str]


class WritingPart1Serializer(SafeSerializer):
    """Serializer for part 1 of a writing test (GET requests)."""
    writing_id: int
    content: str
    answer: Optional[str]
    diagram: Optional[str]
    diagram_data: Optional[dict]


class WritingPart2Serializer(SafeSerializer):
    """Serializer for part 2 of a writing test (GET requests)."""
    writing_id: int
    content: str
    answer: Optional[str]