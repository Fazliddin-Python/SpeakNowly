from tortoise import fields
from ..base import BaseModel
from enum import Enum

class SpeakingStatus(str, Enum):
    STARTED = "started"
    PENDING = "pending"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    EXPIRED = "expired"

class SpeakingPart(str, Enum):
    PART_1 = "Part 1"
    PART_2 = "Part 2"
    PART_3 = "Part 3"

class Speaking(BaseModel):
    status = fields.CharEnumField(SpeakingStatus, default=SpeakingStatus.STARTED, null=True, description="Status")
    user = fields.ForeignKeyField("models.User", related_name="speaking_tests",
        description="User taking the test", on_delete=fields.CASCADE)
    start_time = fields.DatetimeField(null=True, blank=True, description="Start time of the test")
    end_time = fields.DatetimeField(null=True, blank=True, description="End time of the test")

    class Meta:
        table = "speaking"
        verbose_name = "Speaking Test"
        verbose_name_plural = "Speaking Tests"

class SpeakingQuestions(BaseModel):
    speaking = fields.ForeignKeyField("models.Speaking", related_name="questions",
        description="Related speaking test", on_delete=fields.CASCADE)
    part = fields.CharEnumField(SpeakingPart, null=True, description="Part of the speaking test")
    title = fields.TextField(null=True, blank=True, description="Title of the question")
    content = fields.TextField(description="Content of the question")

    class Meta:
        table = "speaking_questions"
        verbose_name = "Speaking Question"
        verbose_name_plural = "Speaking Questions"

class SpeakingAnswers(BaseModel):
    question = fields.OneToOneField("models.SpeakingQuestions", related_name="answer",
        on_delete=fields.CASCADE, description="Related question")
    text_answer = fields.TextField(null=True, blank=True, description="Text answer to the question")
    audio_answer = fields.CharField(max_length=255, null=True, blank=True,
        description="Audio answer file path")

    class Meta:
        table = "speaking_answers"
        verbose_name = "Speaking Answer"
        verbose_name_plural = "Speaking Answers"