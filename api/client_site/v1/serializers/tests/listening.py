import asyncio
from typing import Optional, List, Any, Dict, Union
from datetime import datetime
from pydantic import Field, field_validator, model_validator, HttpUrl, BaseModel, ValidationInfo

from ...serializers.base import BaseSerializer
from models.tests.listening import (
    ListeningQuestionType,
    Listening,
    ListeningPart,
    ListeningSection,
    ListeningQuestion,
    ListeningSession,
    ListeningPartNumber,
)


class UserListeningSessionSerializer(BaseModel):
    id: int = Field(..., description="ID of the listening session")
    user_id: int = Field(..., description="ID of the user")
    exam_id: int = Field(..., description="ID of the exam")
    status: str = Field(..., description="Status of the session")
    start_time: Optional[datetime] = Field(None, description="Start time of the session")
    end_time: Optional[datetime] = Field(None, description="End time of the session")

    @classmethod
    async def from_orm(cls, obj: ListeningSession) -> "UserListeningSessionSerializer":
        return cls(
            id=obj.id,
            user_id=obj.user_id,
            exam_id=obj.exam_id,
            status=obj.status,
            start_time=obj.start_time,
            end_time=obj.end_time,
        )


class ListeningQuestionSerializer(BaseModel):
    id: int = Field(..., description="ID of the question")
    section_id: int = Field(..., description="ID of the parent section")
    index: int = Field(..., description="Position index of the question")
    question_text: Optional[str] = Field(None, description="Text of the question")
    options: Optional[Union[List[str], Dict[str, str]]] = Field(None, description="Answer options for the question")  # <-- исправлено
    correct_answer: Any = Field(..., description="Correct answer")

    @classmethod
    async def from_orm(cls, obj: ListeningQuestion) -> "ListeningQuestionSerializer":
        return cls(
            id=obj.id,
            section_id=obj.section_id,
            index=obj.index,
            question_text=obj.question_text,
            options=obj.options,
            correct_answer=obj.correct_answer,
        )


class ListeningSectionSerializer(BaseModel):
    id: int = Field(..., description="ID of the section")
    part_id: int = Field(..., description="ID of the parent part")
    section_number: int = Field(..., description="Section number")
    start_index: int = Field(..., description="Start index in the audio")
    end_index: int = Field(..., description="End index in the audio")
    question_type: ListeningQuestionType = Field(..., description="Type of questions")
    question_text: Optional[str] = Field(None, description="Text for the section")
    options: Optional[Union[List[str], Dict[str, str]]] = None
    questions: Optional[List[ListeningQuestionSerializer]] = Field(None, description="List of questions")

    class Config:
        from_attributes = True

    @classmethod
    async def from_orm(cls, obj: ListeningSection) -> "ListeningSectionSerializer":
        questions_qs = await obj.questions.order_by("index").all()
        questions = [await ListeningQuestionSerializer.from_orm(q) for q in questions_qs]
        return cls(
            id=obj.id,
            part_id=obj.part_id,
            section_number=obj.section_number,
            start_index=obj.start_index,
            end_index=obj.end_index,
            question_type=obj.question_type,
            question_text=obj.question_text,
            options=obj.options,
            questions=questions,
        )


class ListeningPartSerializer(BaseModel):
    id: int = Field(..., description="ID of the part")
    listening_id: int = Field(..., description="ID of the parent listening")
    part_number: ListeningPartNumber = Field(..., description="Part number")
    audio_file: str = Field(..., description="Audio file URL")
    sections: Optional[List[ListeningSectionSerializer]] = Field(None, description="List of sections in the part")

    @classmethod
    async def from_orm(cls, obj: ListeningPart) -> "ListeningPartSerializer":
        sections_qs = await obj.sections.order_by("section_number").all()
        sections = [await ListeningSectionSerializer.from_orm(s) for s in sections_qs]
        return cls(
            id=obj.id,
            listening_id=obj.listening_id,
            part_number=obj.part_number,
            audio_file=obj.audio_file,
            sections=sections,
        )


class ListeningSerializer(BaseModel):
    id: int = Field(..., description="ID of the listening test")
    title: str = Field(..., description="Title of the listening")
    description: str = Field(..., description="Description of the listening")
    parts: Optional[List[ListeningPartSerializer]] = Field(None, description="List of parts in the listening test")

    @classmethod
    async def from_orm(cls, obj: Listening) -> "ListeningSerializer":
        parts_qs = await obj.parts.order_by("part_number").all()
        parts = [await ListeningPartSerializer.from_orm(p) for p in parts_qs]
        return cls(
            id=obj.id,
            title=obj.title,
            description=obj.description,
            parts=parts,
        )


class ListeningCreateSerializer(BaseSerializer):
    """Create a new Listening test."""
    title: str = Field(..., max_length=255, description="Title of the listening test")
    description: str = Field(..., description="Detailed description of the listening test")

    @field_validator("title")
    def title_must_not_be_empty(cls, v: str) -> str:
        """Title cannot be empty or whitespace."""
        v_stripped = v.strip()
        if not v_stripped:
            raise ValueError("title must not be empty or whitespace")
        return v_stripped

    @field_validator("description")
    def description_must_not_be_empty(cls, v: str) -> str:
        """Description cannot be empty or whitespace."""
        v_stripped = v.strip()
        if not v_stripped:
            raise ValueError("description must not be empty or whitespace")
        return v_stripped


class ListeningPartCreateSerializer(BaseSerializer):
    """Create a new part for an existing Listening test."""
    listening_id: int = Field(..., gt=0, description="ID of the parent listening test")
    part_number: int = Field(..., ge=1, le=4, description="Part number (1-4) of the test")
    audio_file: HttpUrl = Field(..., description="URL to the audio file for this part")

    @field_validator("part_number")
    def part_number_in_enum(cls, v: int) -> int:
        """Part number must be between 1 and 4."""
        if v not in {1, 2, 3, 4}:
            raise ValueError("part_number must be between 1 and 4")
        return v


class ListeningSectionCreateSerializer(BaseSerializer):
    """Create a new section within a Listening part."""
    part_id: int = Field(..., gt=0, description="ID of the parent listening part")
    section_number: int = Field(..., ge=1, description="Section index within the part")
    start_index: int = Field(..., ge=0, description="Start timestamp or index in the audio file")
    end_index: int = Field(..., ge=0, description="End timestamp or index in the audio file")
    question_type: ListeningQuestionType = Field(..., description="Type of questions in this section (enum)")
    question_text: Optional[str] = Field(None, description="Prompt text for the section")
    options: Optional[List[str]] = Field(None, description="Shared options for questions, if applicable")

    @model_validator(mode="after")
    def check_indices_and_options(self) -> "ListeningSectionCreateSerializer":
        start_idx = self.start_index
        end_idx = self.end_index
        qtype = self.question_type
        opts = self.options
        if end_idx < start_idx:
            raise ValueError("end_index must be greater than or equal to start_index")
        if qtype in {ListeningQuestionType.CHOICE, ListeningQuestionType.MULTIPLE_ANSWERS, ListeningQuestionType.MATCHING}:
            if not opts or not isinstance(opts, list):
                raise ValueError(f"For question_type='{qtype.value}', 'options' must be a non-empty list of strings")
            for item in opts:
                if not isinstance(item, str) or not item.strip():
                    raise ValueError("Each element in 'options' must be a non-empty string")
        else:
            self.options = None
            if qtype in {ListeningQuestionType.FORM_COMPLETION, ListeningQuestionType.SENTENCE_COMPLETION, ListeningQuestionType.CLOZE_TEST}:
                qt = self.question_text
                if not qt or not qt.strip():
                    raise ValueError(f"For question_type='{qtype.value}', 'question_text' must be a non-empty string")
        return self

    @field_validator("section_number")
    def section_number_must_be_positive(cls, v: int) -> int:
        """Section number must be at least 1."""
        if v < 1:
            raise ValueError("section_number must be at least 1")
        return v


class ListeningQuestionCreateSerializer(BaseSerializer):
    """Create a new question within a Listening section."""
    section_id: int = Field(..., gt=0, description="ID of the parent listening section")
    index: int = Field(..., ge=1, description="Position index of the question within the section")
    question_text: Optional[str] = Field(None, description="Text of the question")
    options: Optional[List[str]] = Field(None, description="Answer options for choice-type questions")
    correct_answer: Any = Field(..., description="Correct answer (string, list, or dict, depending on type)")

    @field_validator("index")
    def index_positive(cls, v: int) -> int:
        """Index must be at least 1."""
        if v < 1:
            raise ValueError("index must be at least 1")
        return v

    @field_validator("options", mode="before")
    def options_must_be_list_of_strings_if_present(cls, v: Optional[List[Any]]) -> Optional[List[str]]:
        """
        If options are provided, ensure they form a non-empty list of non-empty strings.
        """
        if v is None:
            return None
        if not isinstance(v, list) or not v:
            raise ValueError("options must be a non-empty list of strings")
        validated: List[str] = []
        for item in v:
            if not isinstance(item, str) or not item.strip():
                raise ValueError("Each element in options must be a non-empty string")
            validated.append(item.strip())
        return validated

    @field_validator("correct_answer")
    def validate_correct_answer(cls, v: Any) -> Any:
        """
        correct_answer must be:
          - a non-empty string
          - a non-empty list of strings or ints
          - a non-empty dict with non-empty string keys and string/int values
        """
        if v is None:
            raise ValueError("correct_answer must not be empty")
        if isinstance(v, str):
            if not v.strip():
                raise ValueError("correct_answer string must not be empty or whitespace")
            return v.strip()
        if isinstance(v, list):
            if not v:
                raise ValueError("correct_answer list must not be empty")
            for elem in v:
                if not isinstance(elem, (str, int)):
                    raise ValueError("Elements of correct_answer list must be str or int")
                if isinstance(elem, str) and not elem.strip():
                    raise ValueError("Elements of correct_answer list must not be empty strings")
            return v
        if isinstance(v, dict):
            if not v:
                raise ValueError("correct_answer dict must not be empty")
            for key, val in v.items():
                if not isinstance(key, str) or not key.strip():
                    raise ValueError("Keys of correct_answer dict must be non-empty strings")
                if not isinstance(val, (str, int)):
                    raise ValueError("Values of correct_answer dict must be str or int")
                if isinstance(val, str) and not val.strip():
                    raise ValueError("Values of correct_answer dict must not be empty strings")
            return v
        raise ValueError("correct_answer must be str, int, list, or dict")


class AnswerSerializer(BaseModel):
    """Serializer for a single answer submission."""
    question_id: int = Field(..., description="ID of the question being answered")
    answer: Union[str, int, List[Union[str, int]]] = Field(..., description="User's answer to the question")


class ListeningAnswerSerializer(BaseModel):
    """
    Submit answers for a listening test.
    Expects a list of AnswerSerializer.
    """
    test_id: int = Field(..., description="ID of the listening test")
    answers: List[AnswerSerializer] = Field(..., description="List of answers")


class ExamShortSerializer(BaseModel):
    """Return minimal exam information."""
    id: int = Field(..., description="Unique identifier of the exam")
    title: str = Field(..., description="Title of the exam")
    description: str = Field(..., description="Description of the exam")

    @classmethod
    async def from_orm(cls, obj: Listening) -> "ExamShortSerializer":
        return cls(id=obj.id, title=obj.title, description=obj.description)


class PartSlimSerializer(BaseModel):
    """Return minimal part information."""
    id: int = Field(..., description="Unique identifier of the part")
    part_number: int = Field(..., description="Part number (1-4) of the test")
    audio_file: str = Field(..., description="URL to the audio file for this part")

    @classmethod
    async def from_orm(cls, obj: ListeningPart) -> "PartSlimSerializer":
        return cls(id=obj.id, part_number=obj.part_number, audio_file=obj.audio_file)


class ListeningDataSlimSerializer(BaseModel):
    """Full data for a listening session (exam + parts)."""
    session_id: int = Field(..., description="ID of the listening session")
    start_time: Optional[datetime] = Field(None, description="Start timestamp of the session")
    status: str = Field(..., description="Current status of the session")
    exam: ExamShortSerializer = Field(..., description="Basic exam info")
    parts: List[PartSlimSerializer] = Field(..., description="List of parts in the listening test")
    questions: List[ListeningQuestionSerializer] = Field(..., description="All questions in the session")  # Новое поле

    @classmethod
    async def from_orm(cls, session_obj: ListeningSession) -> "ListeningDataSlimSerializer":
        exam_obj = await session_obj.exam
        exam_serialized = await ExamShortSerializer.from_orm(exam_obj)
        parts_qs = exam_obj.parts.order_by("part_number").all() if hasattr(exam_obj, "parts") else []
        parts_list = [await PartSlimSerializer.from_orm(p) for p in parts_qs]

        # Собираем все вопросы
        questions = []
        for part in parts_qs:
            sections = await part.sections.all()
            for section in sections:
                qs = await section.questions.all()
                for q in qs:
                    questions.append(await ListeningQuestionSerializer.from_orm(q))

        return cls(
            session_id=session_obj.id,
            start_time=session_obj.start_time,
            status=session_obj.status,
            exam=exam_serialized,
            parts=parts_list,
            questions=questions,
        )


class ListeningAnalyseResponseSerializer(BaseModel):
    """Analysis results for a listening session."""
    session_id: int = Field(..., description="ID of the listening session")
    analyse: Dict[str, Any] = Field(..., description="Analysis data for the session")
    responses: List[Dict[str, Any]] = Field(..., description="List of user responses with details")
