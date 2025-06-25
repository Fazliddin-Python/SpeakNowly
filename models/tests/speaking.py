import json
from tortoise import fields
from enum import Enum
from ..base import BaseModel

class SpeakingStatus(str, Enum):
    STARTED = "started"
    PENDING = "pending"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    EXPIRED = "expired"

class SpeakingPart(int, Enum):
    PART_1 = 1
    PART_2 = 2
    PART_3 = 3

class Speaking(BaseModel):
    """Template for a speaking test (set of questions)."""
    title = fields.CharField(max_length=255, description="Test title")
    description = fields.TextField(null=True, description="Test description")

    class Meta:
        table = "speaking"
        verbose_name = "Speaking Test"
        verbose_name_plural = "Speaking Tests"

    def __str__(self):
        return f"Speaking test {self.id} for user {self.user_id}"

class SpeakingSession(BaseModel):
    """User's attempt at a speaking test."""
    user = fields.ForeignKeyField("models.User", related_name="speaking_sessions", on_delete=fields.CASCADE)
    test = fields.ForeignKeyField("models.Speaking", related_name="sessions", on_delete=fields.CASCADE)
    status = fields.CharEnumField(SpeakingStatus, default=SpeakingStatus.PENDING, description="Session status")
    start_time = fields.DatetimeField(null=True)
    end_time = fields.DatetimeField(null=True)

    class Meta:
        table = "speaking_sessions"
        verbose_name = "Speaking Session"
        verbose_name_plural = "Speaking Sessions"

    def __str__(self):
        return f"Session {self.id} for user {self.user_id} (test {self.test_id})"

class SpeakingQuestion(BaseModel):
    """Question belonging to a speaking test template."""
    test = fields.ForeignKeyField("models.Speaking", related_name="questions", on_delete=fields.CASCADE)
    part = fields.IntEnumField(SpeakingPart, description="Part number (1,2,3)")
    title = fields.CharField(max_length=255, null=True)
    content = fields.JSONField(description="Question content")

    class Meta:
        table = "speaking_questions"
        verbose_name = "Speaking Question"
        verbose_name_plural = "Speaking Questions"

    def __str__(self):
        snippet = (json.dumps(self.content) or "")[:50]
        return f"{self.part} for Speaking {self.speaking_id}: {snippet}"

class SpeakingAnswer(BaseModel):
    """User's answer to a speaking question in a session."""
    session = fields.ForeignKeyField("models.SpeakingSession", related_name="answers", on_delete=fields.CASCADE)
    question = fields.ForeignKeyField("models.SpeakingQuestion", related_name="answers", on_delete=fields.CASCADE)
    text_answer = fields.TextField(null=True)
    audio_answer = fields.CharField(max_length=255, null=True)

    class Meta:
        table = "speaking_answers"
        unique_together = ("session", "question")
