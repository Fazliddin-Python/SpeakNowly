from typing import Optional, List, Dict
from pydantic import Field, field_validator
from ..base import BaseSerializer, SafeSerializer
from models.tests.reading import Passage as PassageModel, Question as QuestionModel, Variant as VariantModel
from models.tests.constants import Constants
from datetime import datetime

# -----------------------------
#   Safe (GET) serializers
# -----------------------------

class PassageSerializer(BaseSerializer):
    id: int = Field(..., description="ID of the passage")
    number: int = Field(..., description="Passage number")
    skills: str = Field(..., description="Skills associated with the passage")
    title: str = Field(..., description="Title of the passage")
    text: str = Field(..., description="Text content of the passage")
    level: Optional[Constants.PassageLevel] = Field(Constants.PassageLevel.EASY, description="Passage level (easy/medium/hard)")

class VariantSerializer(BaseSerializer):
    id: int = Field(..., description="ID of the variant")
    question_id: int = Field(..., description="ID of the related question")
    text: str = Field(..., description="Text of the variant")
    is_correct: bool = Field(..., description="Whether this variant is correct")

class QuestionListSerializer(SafeSerializer):
    passage_id: int = Field(..., description="ID of the parent passage")
    text: str = Field(..., description="Text of the question")
    type: Constants.QuestionType = Field(..., description="Type of the question")
    score: int = Field(..., description="Score for the question")
    answers: List[VariantSerializer] = Field(..., description="List of variants for this question")

    @classmethod
    async def from_orm(cls, obj: QuestionModel) -> "QuestionListSerializer":
        variants_qs = await obj.variants.all()
        variants = [VariantSerializer.from_orm(v) for v in variants_qs]
        return cls(
            id=obj.id,
            passage_id=obj.passage_id,
            text=obj.text,
            type=obj.type,
            score=obj.score,
            answers=variants,
            created_at=obj.created_at,
            updated_at=obj.updated_at
        )

class ReadingSerializer(BaseSerializer):
    status: Constants.ReadingStatus = Field(..., description="Status of the test")
    user_id: int = Field(..., description="ID of the user")
    start_time: datetime = Field(..., description="Start time of the test")
    end_time: Optional[datetime] = Field(None, description="End time of the test")
    score: float = Field(..., description="Score of the test")
    duration: int = Field(..., description="Duration in minutes")

class QuestionAnalysisSerializer(BaseSerializer):
    id: int = Field(..., description="ID of the question")
    text: str = Field(..., description="Text of the question")
    type: Constants.QuestionType = Field(..., description="Type of the question")
    answers: List[Dict[str, Optional[str]]] = Field(..., description="List of variants with correctness info")
    
    @classmethod
    async def from_orm(cls, obj: QuestionModel) -> "QuestionAnalysisSerializer":
        variants_qs = await obj.variants.all()
        answers = [
            {"id": v.id, "text": v.text, "is_correct": v.is_correct}
            for v in variants_qs
        ]
        return cls(id=obj.id, text=obj.text, type=obj.type, answers=answers)

# -----------------------------
#   “Create/Update” serializers (admin)
# -----------------------------

class PassageCreateSerializer(BaseSerializer):
    number: int = Field(..., description="Passage number")
    skills: str = Field(..., description="Skills associated with the passage")
    title: str = Field(..., description="Title of the passage")
    text: str = Field(..., description="Text content of the passage")
    level: Constants.PassageLevel = Field(Constants.PassageLevel.EASY, description="Passage level (easy/medium/hard)")

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("title must not be empty")
        return v

    @field_validator("text")
    @classmethod
    def validate_text(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("text must not be empty")
        return v

class QuestionCreateSerializer(BaseSerializer):
    passage_id: int = Field(..., description="ID of the related passage")
    text: str = Field(..., description="Text of the question")
    type: Constants.QuestionType = Field(..., description="Type of the question")
    score: int = Field(..., description="Score for this question")

    @field_validator("text")
    @classmethod
    def validate_text(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("text must not be empty")
        return v

    @field_validator("score")
    @classmethod
    def validate_score(cls, v: int) -> int:
        if v < 0:
            raise ValueError("score must be non-negative")
        return v

class VariantCreateSerializer(BaseSerializer):
    question_id: int = Field(..., description="ID of the related question")
    text: str = Field(..., description="Text of the variant")
    is_correct: bool = Field(False, description="Whether this variant is correct")

    @field_validator("text")
    @classmethod
    def validate_text(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("text must not be empty")
        return v

# -----------------------------
#   “Submit / Finish” serializers (user flow)
# -----------------------------

class SubmitQuestionAnswerSerializer(BaseSerializer):
    question_id: int = Field(..., description="ID of the question")
    answer: str = Field(..., description="User's answer to the question")

class SubmitPassageAnswerSerializer(BaseSerializer):
    answers: List[SubmitQuestionAnswerSerializer] = Field(..., description="List of question-answer pairs")

class FinishReadingSerializer(BaseSerializer):
    reading_id: int = Field(..., description="ID of the reading session to finish")

class StartReadingSerializer(BaseSerializer):
    reading_id: int = Field(..., description="ID of the reading session to start")
