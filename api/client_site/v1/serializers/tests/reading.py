from typing import List, Dict, Any, Optional
from pydantic import Field, field_validator
from datetime import datetime
from ..base import BaseSerializer, SafeSerializer
from models.tests.reading import Passage as PassageModel, Question as QuestionModel, Variant as VariantModel
from models.tests.constants import Constants

# -----------------------------
#   Safe (GET) serializers
# -----------------------------

class StartReadingSerializer(BaseSerializer):
    """Serializer for initiating a reading session."""
    reading_id: int = Field(..., description="ID of the reading session to start")


class VariantSerializer(BaseSerializer):
    """Serializer for a single answer variant (without correctness flag)."""
    id: int = Field(..., description="ID of the variant")
    text: str = Field(..., description="Text content of the variant")

    @classmethod
    async def from_orm(cls, obj: VariantModel) -> "VariantSerializer":
        return cls(
            id=obj.id,
            text=obj.text,
        )


class QuestionListSerializer(SafeSerializer):
    """Serializer for listing questions along with their variants."""
    id: int = Field(..., description="ID of the question")
    text: str = Field(..., description="Text content of the question")
    type: Constants.QuestionType = Field(..., description="Type of the question")
    score: int = Field(..., description="Score assigned to the question")
    answers: List[VariantSerializer] = Field(..., description="List of related answer variants")

    @classmethod
    async def from_orm(cls, obj: QuestionModel) -> "QuestionListSerializer":
        variants = await obj.variants.all()
        answers = [await VariantSerializer.from_orm(v) for v in variants]
        return cls(
            id=obj.id,
            text=obj.text,
            type=obj.type,
            score=obj.score,
            answers=answers,
            created_at=obj.created_at,
            updated_at=obj.updated_at,
        )


class PassageSerializer(BaseSerializer):
    """Serializer for a reading passage and its associated questions."""
    id: int = Field(..., description="ID of the passage")
    number: Optional[int] = Field(None, description="Sequence number of the passage")
    skills: Optional[str] = Field(None, description="Skills tags for the passage")
    title: str = Field(..., description="Title of the passage")
    text: str = Field(..., description="Full text content of the passage")
    level: Constants.PassageLevel = Field(Constants.PassageLevel.EASY, description="Difficulty level of the passage")
    questions: List[QuestionListSerializer] = Field(..., description="List of questions for this passage")

    @classmethod
    async def from_orm(cls, obj: PassageModel) -> "PassageSerializer":
        questions_qs = await obj.questions.all()
        questions = [await QuestionListSerializer.from_orm(q) for q in questions_qs]
        return cls(
            id=obj.id,
            number=obj.number,
            skills=obj.skills,
            title=obj.title,
            text=obj.text,
            level=obj.level,
            questions=questions,
        )

class ReadingSerializer(BaseSerializer):
    """Serializer for reading session with optional related passage and questions."""
    id: int = Field(..., description="ID of the reading session")
    status: str = Field(..., description="Status of the reading session")
    user_id: int = Field(..., description="ID of the user who owns the session")
    start_time: Optional[datetime] = Field(None, description="Time when session started")
    end_time: Optional[datetime] = Field(None, description="Time when session ended")
    score: Optional[int] = Field(None, description="Total score achieved")
    duration: Optional[int] = Field(None, description="Duration in seconds")
    passage: Optional[PassageSerializer] = Field(None, description="Passage with related questions")
    questions: Optional[List[QuestionListSerializer]] = Field(None, description="Questions shown in the session")

    @classmethod
    async def from_orm(cls, obj, detailed: bool = True) -> "ReadingSerializer":
        """Create serializer from ORM object. Supports short and detailed modes."""
        if detailed:
            passage_obj = await obj.passage
            questions_qs = await passage_obj.questions.all()
            questions = [await QuestionListSerializer.from_orm(q) for q in questions_qs]
            passage = await PassageSerializer.from_orm(passage_obj)
        else:
            passage = None
            questions = None

        return cls(
            id=obj.id,
            status=obj.status,
            user_id=obj.user_id,
            start_time=obj.start_time,
            end_time=obj.end_time,
            score=obj.score,
            duration=obj.duration,
            passage=passage,
            questions=questions,
            created_at=obj.created_at,
            updated_at=obj.updated_at,
        )

# -----------------------------
#   Create/Update (admin) serializers
# -----------------------------

class PassageCreateSerializer(BaseSerializer):
    """Serializer for creating or updating a passage."""
    number: int = Field(..., description="Sequence number of the passage")
    skills: str = Field(..., description="Skills tags for the passage")
    title: str = Field(..., description="Title of the passage")
    text: str = Field(..., description="Full text content of the passage")
    level: Constants.PassageLevel = Field(Constants.PassageLevel.EASY, description="Difficulty level of the passage")

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Title must not be empty")
        return v

    @field_validator("text")
    @classmethod
    def validate_text(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Text must not be empty")
        return v


class QuestionCreateSerializer(BaseSerializer):
    """Serializer for creating or updating a question."""
    passage_id: int = Field(..., description="ID of the related passage")
    text: str = Field(..., description="Text content of the question")
    type: Constants.QuestionType = Field(..., description="Type of the question")
    score: int = Field(..., description="Score assigned to the question")

    @field_validator("text")
    @classmethod
    def validate_text(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Question text must not be empty")
        return v

    @field_validator("score")
    @classmethod
    def validate_score(cls, v: int) -> int:
        if v < 0:
            raise ValueError("Score must be non-negative")
        return v


class VariantCreateSerializer(BaseSerializer):
    """Serializer for creating or updating a variant."""
    question_id: int = Field(..., description="ID of the related question")
    text: str = Field(..., description="Text content of the variant")
    is_correct: bool = Field(False, description="Flag indicating if this variant is correct")

    @field_validator("text")
    @classmethod
    def validate_text(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Variant text must not be empty")
        return v

# -----------------------------
#   Submit / Finish (user flow) serializers
# -----------------------------

class SubmitQuestionAnswerSerializer(BaseSerializer):
    """Serializer for a user's answer to a single question."""
    question_id: int = Field(..., description="ID of the question being answered")
    answer: str = Field(..., description="User's submitted answer text or variant ID as string")


class SubmitPassageAnswerSerializer(BaseSerializer):
    """Serializer for submitting answers to all questions in a passage."""
    # reading_id: int = Field(..., description="ID of the reading session")
    passage_id: int = Field(..., description="ID of the passage being answered")
    answers: List[SubmitQuestionAnswerSerializer] = Field(
        ..., description="List of question-answer pairs"
    )


class FinishReadingSerializer(BaseSerializer):
    """Serializer for marking a reading session as completed."""
    reading_id: int = Field(..., description="ID of the reading session to finish")


# -----------------------------
#   Analysis serializers
# -----------------------------

class QuestionAnalysisSerializer(SafeSerializer):
    """Serializer for detailed analysis of a question, including correctness flags."""
    id: int = Field(..., description="ID of the question")
    text: str = Field(..., description="Text content of the question")
    type: Constants.QuestionType = Field(..., description="Type of the question")
    answers: List[Dict[str, Any]] = Field(
        ..., description="List of answer variants with correctness information"
    )

    @classmethod
    async def from_orm(cls, obj: QuestionModel) -> "QuestionAnalysisSerializer":
        variants = await obj.variants.all()
        answers = [
            {"id": v.id, "text": v.text, "is_correct": v.is_correct}
            for v in variants
        ]
        return cls(
            id=obj.id,
            text=obj.text,
            type=obj.type,
            answers=answers,
            created_at=obj.created_at,
            updated_at=obj.updated_at,
        )

class ReadingAnalyseResponseSerializer(BaseSerializer):
    """Serializer for summarizing analysis results of a reading session."""
    reading_id: int = Field(..., description="ID of the reading session")
    analyse: Dict[str, Any] = Field(..., description="Overall analysis summary, including scores and feedback")
    responses: List[Dict[str, Any]] = Field(..., description="List of per-question analysis details")
