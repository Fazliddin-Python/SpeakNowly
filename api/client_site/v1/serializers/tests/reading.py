from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from ..base import BaseSerializer, SafeSerializer
from models.tests.reading import Passage as PassageModel, Question as QuestionModel, Variant as VariantModel


class StartReadingSerializer(BaseSerializer):
    reading_id: int = Field(..., description="ID of the reading session to start")


class VariantSerializer(BaseModel):
    id: int = Field(..., description="ID of the variant")
    text: str = Field(..., description="Text of the variant")

    class Config:
        from_attributes = True

    @classmethod
    async def from_orm(cls, obj: VariantModel) -> "VariantSerializer":
        return cls(id=obj.id, text=obj.text)


class QuestionListSerializer(BaseModel):
    id: int = Field(..., description="ID of the question")
    text: str = Field(..., description="Text of the question")
    answers: List[VariantSerializer] = Field(..., description="List of variants for this question")

    class Config:
        from_attributes = True

    @classmethod
    async def from_orm(cls, obj: QuestionModel) -> "QuestionListSerializer":
        variants_qs = await obj.variants.all()
        variants = [await VariantSerializer.from_orm(v) for v in variants_qs]
        return cls(id=obj.id, text=obj.text, answers=variants)


class PassageSerializer(BaseModel):
    id: int = Field(..., description="ID of the passage")
    title: str = Field(..., description="Title of the passage")
    text: str = Field(..., description="Text content of the passage")
    questions: List[QuestionListSerializer] = Field(..., description="List of questions under this passage")

    class Config:
        from_attributes = True

    @classmethod
    async def from_orm(cls, obj: PassageModel) -> "PassageSerializer":
        questions_qs = await obj.questions.all()
        questions = [await QuestionListSerializer.from_orm(q) for q in questions_qs]
        return cls(id=obj.id, title=obj.title, text=obj.text, questions=questions)


class SubmitQuestionAnswerSerializer(BaseModel):
    question_id: int = Field(..., description="ID of the question")
    answer: str = Field(..., description="User's answer to the question")


class SubmitPassageAnswerSerializer(BaseModel):
    reading_id: int = Field(..., description="ID of the reading session")
    passage_id: int = Field(..., description="ID of the passage")
    answers: List[SubmitQuestionAnswerSerializer] = Field(..., description="List of question-answer pairs")


class FinishReadingSerializer(BaseModel):
    reading_id: int = Field(..., description="ID of the reading session to finish")


class QuestionAnalysisSerializer(BaseModel):
    id: int = Field(..., description="ID of the question")
    text: str = Field(..., description="Text of the question")
    type: str = Field(..., description="Type of the question")
    answers: List[Dict[str, Any]] = Field(..., description="List of variants with correctness info")

    class Config:
        from_attributes = True

    @classmethod
    async def from_orm(cls, obj: QuestionModel) -> "QuestionAnalysisSerializer":
        variants_qs = await obj.variants.all()
        answers = [
            {"id": v.id, "text": v.text, "is_correct": v.is_correct}
            for v in variants_qs
        ]
        return cls(id=obj.id, text=obj.text, type=obj.type, answers=answers)


# -----------------------------
#   Admin / Create & Update
# -----------------------------
class PassageCreateSerializer(BaseSerializer):
    number: int = Field(..., description="Passage number")
    skills: str = Field(..., description="Skills associated with the passage")
    title: str = Field(..., description="Title of the passage")
    text: str = Field(..., description="Text content of the passage")

    @classmethod
    def validate_title(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("title must not be empty")
        return v

    @classmethod
    def validate_text(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("text must not be empty")
        return v


class QuestionCreateSerializer(BaseSerializer):
    passage_id: int = Field(..., description="ID of the related passage")
    text: str = Field(..., description="Text of the question")
    type: str = Field(..., description="Type of the question")
    score: int = Field(..., description="Score for this question")
    correct_answer: Optional[str] = Field(None, description="Correct answer text (if applicable)")

    @classmethod
    def validate_text(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("text must not be empty")
        return v

    @classmethod
    def validate_score(cls, v: int) -> int:
        if v < 0:
            raise ValueError("score must be non-negative")
        return v


class VariantCreateSerializer(BaseSerializer):
    question_id: int = Field(..., description="ID of the related question")
    text: str = Field(..., description="Text of the variant")
    is_correct: bool = Field(False, description="Whether this variant is correct")

    @classmethod
    def validate_text(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("text must not be empty")
        return v
