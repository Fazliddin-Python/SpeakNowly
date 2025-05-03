from tortoise import fields
from ..base import BaseModel

class Listening(BaseModel):
    title = fields.CharField(max_length=255, description="Title of the listening test")
    description = fields.TextField(description="Description of the listening test")

    class Meta:
        table = "listenings"
        verbose_name = "Listening Test"
        verbose_name_plural = "Listening Tests"

class ListeningPart(BaseModel):
    listening = fields.ForeignKeyField("models.Listening", on_delete=fields.CASCADE, related_name="parts", description="Related listening test")
    part_number = fields.IntField(choices=[(1, "Part 1"), (2, "Part 2"), (3, "Part 3"), (4, "Part 4")], description="Part number of the test")
    audio_file = fields.CharField(max_length=255, description="Audio file path")

    class Meta:
        table = "listening_parts"
        verbose_name = "Listening Part"
        verbose_name_plural = "Listening Parts"

class ListeningSection(BaseModel):
    part = fields.ForeignKeyField("models.ListeningPart", on_delete=fields.CASCADE, related_name="sections", description="Related listening part")
    section_number = fields.IntField(description="Section number within the part")
    start_index = fields.IntField(description="Start index of the section")
    end_index = fields.IntField(description="End index of the section")
    question_type = fields.CharField(max_length=50, choices=[("form_completion", "Form Completion"), ("choice", "Choice"), ("multiple_answers", "Multiple Answers"), ("matching", "Matching"), ("sentence_completion", "Sentence Completion"), ("cloze_test", "Cloze Test")], description="Type of questions in the section")
    question_text = fields.TextField(null=True, description="Question text for the section")
    options = fields.JSONField(null=True, description="Options for the questions in the section")

    class Meta:
        table = "listening_sections"
        verbose_name = "Listening Section"
        verbose_name_plural = "Listening Sections"

class ListeningQuestion(BaseModel):
    section = fields.ForeignKeyField("models.ListeningSection", on_delete=fields.CASCADE, related_name="questions", description="Related section")
    index = fields.IntField(description="Index of the question within the section")
    options = fields.JSONField(null=True, description="Options for the question")
    correct_answer = fields.JSONField(description="Correct answer for the question")

    class Meta:
        table = "listening_questions"
        verbose_name = "Listening Question"
        verbose_name_plural = "Listening Questions"

class UserListeningSession(BaseModel):
    status = fields.CharField(max_length=15, choices=[("started", "Started"), ("pending", "Pending"), ("cancelled", "Cancelled"), ("completed", "Completed"), ("expired", "Expired")], default="started", null=True, description="Status of the user's listening session")
    user = fields.ForeignKeyField("models.User", on_delete=fields.CASCADE, related_name="listening_sessions", description="Related user")
    exam = fields.ForeignKeyField("models.Listening", on_delete=fields.CASCADE, related_name="user_sessions", description="Related listening exam")
    start_time = fields.DatetimeField(auto_now_add=True, description="Start time of the session")
    end_time = fields.DatetimeField(null=True, description="End time of the session")

    class Meta:
        table = "user_listening_sessions"
        verbose_name = "User Listening Session"
        verbose_name_plural = "User Listening Sessions"

class UserResponse(BaseModel):
    session = fields.ForeignKeyField("models.UserListeningSession", on_delete=fields.CASCADE, related_name="responses", description="Related session")
    user = fields.ForeignKeyField("models.User", on_delete=fields.CASCADE, description="User who provided the response")
    question = fields.ForeignKeyField("models.ListeningQuestion", on_delete=fields.CASCADE, description="Related question")
    user_answer = fields.JSONField(description="User's answer to the question")
    is_correct = fields.BooleanField(default=False, description="Whether the user's answer is correct")
    score = fields.IntField(default=0, description="Score for the response")

    class Meta:
        table = "user_responses"
        verbose_name = "User Response"
        verbose_name_plural = "User Responses"
