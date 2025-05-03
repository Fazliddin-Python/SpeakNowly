from tortoise import fields
from ..base import BaseModel

class Speaking(BaseModel):
    status = fields.CharField(max_length=15, choices=[
        ("started", "Started"), ("pending", "Pending"), ("cancelled", "Cancelled"),
        ("completed", "Completed"), ("expired", "Expired")], default="", null=True,
        blank=True, description="Status of the speaking test")
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
    part = fields.CharField(max_length=10, choices=[
        ("Part 1", "Part 1 - Introduction"), ("Part 2", "Part 2 - Long Turn"),
        ("Part 3", "Part 3 - Discussion")], null=True, blank=True,
        description="Part of the speaking test")
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
    audio_answer = fields.CharField(max_length=255, upload_to="audio_responses/", null=True, blank=True,
        description="Audio answer to the question")

    class Meta:
        table = "speaking_answers"
        verbose_name = "Speaking Answer"
        verbose_name_plural = "Speaking Answers"
