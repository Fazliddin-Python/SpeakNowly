from datetime import datetime
from typing import Optional
from ..base import BaseSerializer, SafeSerializer


class WritingPart1Serializer(BaseSerializer):
    """Serializer for part 1 of a writing test (GET requests)."""
    id: int
    writing_id: int
    content: str
    answer: Optional[str]
    diagram: Optional[str]
    diagram_data: Optional[dict]


class WritingPart2Serializer(BaseSerializer):
    """Serializer for part 2 of a writing test (GET requests)."""
    id: int
    writing_id: int
    content: str
    answer: Optional[str]


class WritingSerializer(BaseSerializer):
    id: int
    user_id: int
    start_time: datetime
    end_time: Optional[datetime]
    status: str
    part1: Optional[WritingPart1Serializer]
    part2: Optional[WritingPart2Serializer]