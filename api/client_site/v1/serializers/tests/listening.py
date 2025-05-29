import asyncio
from typing import Optional, List, Any, Dict, Union
from datetime import datetime
from pydantic import Field
from ...serializers.base import BaseSerializer, SafeSerializer

# --- For creation (POST) ---
class ListeningCreateSerializer(BaseSerializer):
    """Serializer for creating a Listening test."""
    title: str = Field(..., max_length=255, description="Title of the listening test")
    description: str = Field(..., description="Detailed description of the listening test")

class ListeningPartCreateSerializer(BaseSerializer):
    """Serializer for creating a part within a Listening test."""
    listening_id: int = Field(..., gt=0, description="ID of the parent listening test")
    part_number: int = Field(..., ge=1, le=4, description="Part number (1-4) of the test")
    audio_file: str = Field(..., description="Path or URL to the audio file for this part")

class ListeningSectionCreateSerializer(BaseSerializer):
    """Serializer for creating a section within a listening part."""
    part_id: int = Field(..., gt=0, description="ID of the parent listening part")
    section_number: int = Field(..., ge=1, description="Section index within the part")
    start_index: int = Field(..., ge=0, description="Start timestamp or index in the audio file")
    end_index: int = Field(..., ge=0, description="End timestamp or index in the audio file")
    question_type: str = Field(..., description="Type of questions in this section (enum)")
    question_text: Optional[str] = Field(None, description="Prompt text for the section")
    options: Optional[List[str]] = Field(None, description="Shared options for questions, if applicable")

class ListeningQuestionCreateSerializer(BaseSerializer):
    """Serializer for creating a question within a section."""
    section_id: int = Field(..., gt=0, description="ID of the parent listening section")
    index: int = Field(..., ge=1, description="Position index of the question within the section")
    options: Optional[List[str]] = Field(None, description="Answer options for choice-type questions")
    correct_answer: Any = Field(..., description="Correct answer (string or list, depending on type)")

class UserResponseCreateSerializer(BaseSerializer):
    """Serializer for submitting a user's answer to a question. Session and user are inferred."""
    question_id: int = Field(..., gt=0, description="ID of the question being answered")
    user_answer: Any = Field(..., description="User-provided answer (string, list, etc.)")

# --- For reading (GET) ---

class ExamShortSerializer(SafeSerializer):
    title: str
    description: str

    @classmethod
    async def from_orm(cls, obj):
        return cls(
            id=obj.id,
            title=obj.title,
            description=obj.description,
        )

class ListeningQuestionOptionSerializer(SafeSerializer):
    options: Union[Dict[str, Union[str, int]], List[str]]
    question_text: Optional[str]

class ListeningQuestionSerializer(SafeSerializer):
    """Serializer for reading a question with options and correct answer."""
    section_id: int
    index: int
    options: Optional[Union[dict, list, str, int]]
    correct_answer: Any

    @classmethod
    async def from_orm(cls, obj):
        return cls(
            id=obj.id,
            section_id=obj.section_id,
            index=obj.index,
            options=obj.options,
            correct_answer=obj.correct_answer,
            created_at=getattr(obj, "created_at", None),
            updated_at=getattr(obj, "updated_at", None),
        )

class ListeningSectionSerializer(SafeSerializer):
    """Serializer for reading a section with nested questions."""
    part_id: int
    section_number: int
    start_index: int
    end_index: int
    question_type: str
    question_text: Optional[str]
    options: Optional[List[str]]
    questions: List[ListeningQuestionSerializer]

    @classmethod
    async def from_orm(cls, obj):
        questions = await obj.questions.all() if hasattr(obj, "questions") else []
        serialized = [await ListeningQuestionSerializer.from_orm(q) for q in questions]
        return cls(
            id=obj.id,
            part_id=obj.part_id,
            section_number=obj.section_number,
            start_index=obj.start_index,
            end_index=obj.end_index,
            question_type=obj.question_type,
            question_text=obj.question_text,
            options=obj.options,
            questions=serialized,
            created_at=getattr(obj, "created_at", None),
            updated_at=getattr(obj, "updated_at", None),
        )

class ListeningPartSerializer(SafeSerializer):
    """Serializer for reading a part with nested sections."""
    listening_id: int
    part_number: int
    audio_file: str
    sections: List[ListeningSectionSerializer]

    @classmethod
    async def from_orm(cls, obj):
        sections = await obj.sections.all() if hasattr(obj, "sections") else []
        serialized = [await ListeningSectionSerializer.from_orm(s) for s in sections]
        return cls(
            id=obj.id,
            listening_id=obj.listening_id,
            part_number=obj.part_number,
            audio_file=obj.audio_file,
            sections=serialized,
            created_at=getattr(obj, "created_at", None),
            updated_at=getattr(obj, "updated_at", None),
        )

class ListeningSerializer(SafeSerializer):
    """Serializer for reading listening test with nested parts."""
    title: str = Field(..., description="Title of the listening test")
    description: str = Field(..., description="Description of the listening test")
    parts: List[ListeningPartSerializer] = Field(
        default_factory=list,
        description="List of nested parts within the test"
    )

    @classmethod
    async def from_orm(cls, obj):
        parts = await obj.parts.all() if hasattr(obj, "parts") else []
        serialized = [await ListeningPartSerializer.from_orm(p) for p in parts]
        return cls(
            id=obj.id,
            title=obj.title,
            description=obj.description,
            parts=serialized,
            created_at=getattr(obj, "created_at", None),
            updated_at=getattr(obj, "updated_at", None),
        )

class ListeningDataSerializer(SafeSerializer):
    """Serializer for sending all data for a listening session to the frontend."""
    session_id: int
    start_time: Optional[datetime]
    status: str
    exam: ExamShortSerializer
    parts: List[ListeningPartSerializer]

class UserListeningSessionSerializer(SafeSerializer):
    """Serializer for reading user session details."""
    id: int
    user_id: int
    exam_id: int
    status: str
    start_time: datetime
    end_time: Optional[datetime]
    exam: ExamShortSerializer

    @classmethod
    async def from_orm(cls, obj):
        exam_obj = await obj.exam
        exam_serialized = await ExamShortSerializer.from_orm(exam_obj)
        return cls(
            id=obj.id,
            created_at=getattr(obj, "created_at", None),
            updated_at=getattr(obj, "updated_at", None),
            user_id=obj.user_id,
            exam_id=obj.exam_id,
            status=obj.status,
            start_time=obj.start_time,
            end_time=obj.end_time,
            exam=exam_serialized,
        )

class UserResponseSerializer(BaseSerializer):
    """Serializer for reading user responses to questions."""
    session_id: int = Field(..., description="ID of the listening session")
    user_id: int = Field(..., description="ID of the user")
    question_id: int = Field(..., description="ID of the question")
    user_answer: Any = Field(..., description="User's submitted answer")
    is_correct: bool = Field(..., description="Whether the answer was correct")
    score: int = Field(..., description="Score awarded for the response")


# Для приёма ответов
class AnswerSerializer(BaseSerializer):
    question_id: int
    answer: Union[str, int, list]

class ListeningAnswerSerializer(BaseSerializer):
    test_id: int
    answers: Dict[str, List[AnswerSerializer]]

# Для анализа
class ListeningAnalyseResponseSerializer(SafeSerializer):
    session_id: int
    analyse: Dict[str, Any]
    responses: List[Dict[str, Any]]
