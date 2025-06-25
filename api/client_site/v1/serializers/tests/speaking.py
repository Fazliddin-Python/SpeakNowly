from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class QuestionPartSerializer(BaseModel):
    """Serializer for a single speaking question part."""
    id: int = Field(..., description="ID of the question")
    title: str = Field(..., description="Title of the question")
    content: list = Field(..., description="Content of the question")

    @classmethod
    async def from_orm(cls, obj) -> "QuestionPartSerializer":
        return cls(
            id=obj.id,
            title=obj.title,
            content=obj.content,
        )

class QuestionsSerializer(BaseModel):
    """Serializer for all three speaking question parts."""
    part1: QuestionPartSerializer = Field(..., description="Part 1 question")
    part2: QuestionPartSerializer = Field(..., description="Part 2 question")
    part3: QuestionPartSerializer = Field(..., description="Part 3 question")

    @classmethod
    async def from_orm(cls, speaking_obj, questions_qs) -> "QuestionsSerializer":
        parts = {q.part: q for q in questions_qs}
        return cls(
            part1=await QuestionPartSerializer.from_orm(parts.get(1)),
            part2=await QuestionPartSerializer.from_orm(parts.get(2)),
            part3=await QuestionPartSerializer.from_orm(parts.get(3)),
        )

class AnalyseSerializer(BaseModel):
    """Serializer for IELTS speaking analysis."""
    id: int = Field(..., description="ID of the analysis")
    speaking: int = Field(..., description="Speaking test ID")
    feedback: str = Field(..., description="General feedback")
    overall_band_score: str = Field(..., description="Overall band score")
    fluency_and_coherence_score: str = Field(..., description="Fluency and coherence score")
    fluency_and_coherence_feedback: str = Field(..., description="Fluency and coherence feedback")
    lexical_resource_score: str = Field(..., description="Lexical resource score")
    lexical_resource_feedback: str = Field(..., description="Lexical resource feedback")
    grammatical_range_and_accuracy_score: str = Field(..., description="Grammatical range and accuracy score")
    grammatical_range_and_accuracy_feedback: str = Field(..., description="Grammatical range and accuracy feedback")
    pronunciation_score: str = Field(..., description="Pronunciation score")
    pronunciation_feedback: str = Field(..., description="Pronunciation feedback")

    @classmethod
    async def from_orm(cls, obj) -> "AnalyseSerializer":
        return cls(
            id=obj.id,
            speaking=obj.speaking_id,
            feedback=obj.feedback,
            overall_band_score=obj.overall_band_score,
            fluency_and_coherence_score=obj.fluency_and_coherence_score,
            fluency_and_coherence_feedback=obj.fluency_and_coherence_feedback,
            lexical_resource_score=obj.lexical_resource_score,
            lexical_resource_feedback=obj.lexical_resource_feedback,
            grammatical_range_and_accuracy_score=obj.grammatical_range_and_accuracy_score,
            grammatical_range_and_accuracy_feedback=obj.grammatical_range_and_accuracy_feedback,
            pronunciation_score=obj.pronunciation_score,
            pronunciation_feedback=obj.pronunciation_feedback,
        )

class PartAnalyseSerializer(BaseModel):
    part: int
    fluency_and_coherence_score: float
    fluency_and_coherence_feedback: str
    lexical_resource_score: float
    lexical_resource_feedback: str
    grammatical_range_and_accuracy_score: float
    grammatical_range_and_accuracy_feedback: str
    pronunciation_score: float
    pronunciation_feedback: str
    duration: Optional[float] = None

    @classmethod
    async def from_orm_async(cls, obj):
        return cls(
            part=obj.part,
            fluency_and_coherence_score=obj.fluency_and_coherence_score,
            fluency_and_coherence_feedback=obj.fluency_and_coherence_feedback,
            lexical_resource_score=obj.lexical_resource_score,
            lexical_resource_feedback=obj.lexical_resource_feedback,
            grammatical_range_and_accuracy_score=obj.grammatical_range_and_accuracy_score,
            grammatical_range_and_accuracy_feedback=obj.grammatical_range_and_accuracy_feedback,
            pronunciation_score=obj.pronunciation_score,
            pronunciation_feedback=obj.pronunciation_feedback,
            duration=obj.duration.total_seconds() if obj.duration else None,
        )

class SpeakingAnalysisResponseSerializer(BaseModel):
    analysis: List[PartAnalyseSerializer]
    overall_band_score: float
    feedback: str

    @classmethod
    async def from_orm_async(cls, analysis_objs, overall_band_score, feedback):
        analysis = [await PartAnalyseSerializer.from_orm_async(obj) for obj in analysis_objs]
        return cls(
            analysis=analysis,
            overall_band_score=overall_band_score,
            feedback=feedback
        )

class SpeakingSerializer(BaseModel):
    """Serializer for a speaking test with questions and analysis."""
    id: int = Field(..., description="ID of the speaking test")
    start_time: Optional[datetime] = Field(None, description="Start time")
    end_time: Optional[datetime] = Field(None, description="End time")
    status: str = Field(..., description="Status")
    questions: QuestionsSerializer = Field(..., description="Questions for all parts")
    analyse: Optional[AnalyseSerializer] = Field(None, description="Analysis result")

    @classmethod
    async def from_orm(cls, obj) -> "SpeakingSerializer":
        questions_qs = await obj.questions.all()
        questions = await QuestionsSerializer.from_orm(obj, questions_qs)
        analyse_obj = await obj.analyse
        analyse = await AnalyseSerializer.from_orm(analyse_obj) if analyse_obj else None
        return cls(
            id=obj.id,
            start_time=obj.start_time,
            end_time=obj.end_time,
            status=obj.status,
            questions=questions,
            analyse=analyse,
        )