from enum import Enum
from tortoise import fields
from ..base import BaseModel

class WritingStatus(str, Enum):
    """Status of a writing test."""
    STARTED = "started"
    PENDING = "pending"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    EXPIRED = "expired"

class Writing(BaseModel):
    """Template for a writing test (set of tasks)."""
    title = fields.CharField(max_length=255, description="Test title")
    description = fields.TextField(null=True, description="Test description")

    class Meta:
        table = "writings"

class WritingTask(BaseModel):
    """Task belonging to a writing test template (Task 1 or 2)."""
    test = fields.ForeignKeyField("models.Writing", related_name="tasks", on_delete=fields.CASCADE)
    part = fields.IntField(description="Task number (1 or 2)")
    content = fields.TextField(description="Task content")
    diagram = fields.CharField(max_length=255, null=True, description="Diagram file path")
    diagram_data = fields.JSONField(null=True, description="Diagram data")

    class Meta:
        table = "writing_tasks"

class WritingSession(BaseModel):
    """User's attempt at a writing test."""
    user = fields.ForeignKeyField("models.User", related_name="writing_sessions", on_delete=fields.CASCADE)
    test = fields.ForeignKeyField("models.Writing", related_name="sessions", on_delete=fields.CASCADE)
    status = fields.CharEnumField(WritingStatus, default=WritingStatus.PENDING, description="Session status")
    start_time = fields.DatetimeField(null=True)
    end_time = fields.DatetimeField(null=True)

    class Meta:
        table = "writing_sessions"

class WritingAnswer(BaseModel):
    """User's answer to a writing task in a session."""
    session = fields.ForeignKeyField("models.WritingSession", related_name="answers", on_delete=fields.CASCADE)
    task = fields.ForeignKeyField("models.WritingTask", related_name="answers", on_delete=fields.CASCADE)
    answer = fields.TextField(null=True)

    class Meta:
        table = "writing_answers"
        unique_together = ("session", "task")
