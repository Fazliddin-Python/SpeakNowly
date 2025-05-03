from tortoise import fields
from ..base import BaseModel
from .constants import Constants  # Importing Constants to resolve the error

class Reading(BaseModel):
    status = fields.CharEnumField(
        enum_type=Constants.ReadingStatus, default=Constants.ReadingStatus.PENDING, description="Status of the test"
    )
    user = fields.ForeignKeyField('models.User', related_name='reading_sessions', on_delete=fields.CASCADE, description="Related user")
    passages = fields.ManyToManyField('models.Passage', related_name='readings', description="Related passages")
    start_time = fields.DatetimeField(description="Start time of the test")
    end_time = fields.DatetimeField(null=True, description="End time of the test")
    score = fields.DecimalField(max_digits=3, decimal_places=1, description="Score of the test")
    duration = fields.IntField(default=60, description="Duration in minutes")

    class Meta:
        table = "readings"
        verbose_name = "Reading"
        verbose_name_plural = "Readings"

    def __str__(self) -> str:
        passages_titles = ", ".join([p.title for p in self.passages.all()[:3]])
        return f"{self.user.get_full_name()} - {self.status} - {passages_titles}"

class Answer(BaseModel):
    ANSWERED = "answered"
    NOT_ANSWERED = "not_answered"

    status = fields.CharField(max_length=12, default=NOT_ANSWERED, description="Status of the answer")
    user = fields.ForeignKeyField('models.User', related_name='user_answers', on_delete=fields.CASCADE, description="Related user")
    question = fields.ForeignKeyField('models.Question', related_name='answers', on_delete=fields.CASCADE, description="Related question")
    variant = fields.ForeignKeyField('models.Variant', related_name='user_answers', null=True, on_delete=fields.SET_NULL, description="Selected variant")
    text = fields.TextField(description="Answer text")
    explanation = fields.TextField(null=True, description="Explanation for the answer")
    is_correct = fields.BooleanField(default=False, description="Whether the answer is correct")
    correct_answer = fields.TextField(null=True, default="default", description="Correct answer text")

    class Meta:
        table = "reading_answers"
        verbose_name = "Answer"
        verbose_name_plural = "Answers"

    def __str__(self) -> str:
        return f"Answer to {self.question.text}"
    
class Passage(BaseModel):
    level = fields.CharField(max_length=50, description="Difficulty level of the passage")
    number = fields.IntField(description="Number of the passage")
    title = fields.CharField(max_length=255, description="Title of the passage")
    text = fields.TextField(description="Text content of the passage")
    skills = fields.JSONField(description="Skills associated with the passage")

    class Meta:
        table = "reading_passages"
        verbose_name = "Passage"
        verbose_name_plural = "Passages"

    def __str__(self) -> str:
        return self.title
    
class Question(BaseModel):
    passage = fields.ForeignKeyField('models.Passage', related_name='questions', on_delete=fields.CASCADE, description="Related passage")
    text = fields.TextField(description="Text of the question")
    type = fields.CharField(max_length=50, description="Type of the question")
    score = fields.IntField(description="Score for the question")
    correct_answer = fields.TextField(description="Correct answer for the question")

    class Meta:
        table = "reading_questions"
        verbose_name = "Question"
        verbose_name_plural = "Questions"

    def __str__(self) -> str:
        return self.text
    
class Variant(BaseModel):
    question = fields.ForeignKeyField('models.Question', related_name='variants', on_delete=fields.CASCADE, description="Related question")
    text = fields.TextField(description="Text of the variant")
    is_correct = fields.BooleanField(default=False, description="Whether the variant is correct")

    class Meta:
        table = "reading_variants"
        verbose_name = "Variant"
        verbose_name_plural = "Variants"

    def __str__(self) -> str:
        return f"Variant for {self.question.text}"