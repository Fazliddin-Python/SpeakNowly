from tortoise import fields
from .base import BaseModel

class ListeningAnalyse(BaseModel):
    listening = fields.OneToOneField('models.Listening', related_name='analyse', description="Related listening test")
    correct_answers = fields.IntField(default=0, description="Number of correct answers")
    overall_score = fields.DecimalField(max_digits=3, decimal_places=1, description="Overall score")
    timing = fields.TimeField(description="Time taken")
    feedback = fields.TextField(description="Feedback for the test")

    class Meta:
        table = "listening_analyses"
        verbose_name = "Listening Analyse"
        verbose_name_plural = "Listening Analyses"

    def __str__(self):
        return f"Listening Analyse - Score: {self.overall_score}"


class WritingAnalyse(BaseModel):
    writing = fields.OneToOneField('models.Writing', related_name='analyse', description="Related writing test")
    task_achievement_feedback = fields.TextField(description="Feedback on task achievement")
    task_achievement_score = fields.DecimalField(max_digits=3, decimal_places=1, description="Score for task achievement")
    lexical_resource_feedback = fields.TextField(description="Feedback on lexical resource")
    lexical_resource_score = fields.DecimalField(max_digits=3, decimal_places=1, description="Score for lexical resource")
    coherence_and_cohesion_feedback = fields.TextField(description="Feedback on coherence and cohesion")
    coherence_and_cohesion_score = fields.DecimalField(max_digits=3, decimal_places=1, description="Score for coherence and cohesion")
    grammatical_range_and_accuracy_feedback = fields.TextField(description="Feedback on grammar")
    grammatical_range_and_accuracy_score = fields.DecimalField(max_digits=3, decimal_places=1, description="Score for grammar")
    overall_band_score = fields.DecimalField(max_digits=3, decimal_places=1, description="Overall band score")
    total_feedback = fields.TextField(description="Overall feedback")

    class Meta:
        table = "writing_analyses"
        verbose_name = "Writing Analyse"
        verbose_name_plural = "Writing Analyses"

    def __str__(self):
        return f"Writing Analyse - Score: {self.overall_band_score}"


class SpeakingAnalyse(BaseModel):
    speaking = fields.OneToOneField('models.Speaking', related_name='analyse', description="Related speaking test")
    fluency_and_coherence_feedback = fields.TextField(description="Feedback on fluency and coherence")
    fluency_and_coherence_score = fields.DecimalField(max_digits=3, decimal_places=1, description="Score for fluency and coherence")
    lexical_resource_feedback = fields.TextField(description="Feedback on lexical resource")
    lexical_resource_score = fields.DecimalField(max_digits=3, decimal_places=1, description="Score for lexical resource")
    grammatical_range_and_accuracy_feedback = fields.TextField(description="Feedback on grammar")
    grammatical_range_and_accuracy_score = fields.DecimalField(max_digits=3, decimal_places=1, description="Score for grammar")
    pronunciation_feedback = fields.TextField(description="Feedback on pronunciation")
    pronunciation_score = fields.DecimalField(max_digits=3, decimal_places=1, description="Score for pronunciation")
    overall_band_score = fields.DecimalField(max_digits=3, decimal_places=1, description="Overall band score")
    total_feedback = fields.TextField(description="Overall feedback")

    class Meta:
        table = "speaking_analyses"
        verbose_name = "Speaking Analyse"
        verbose_name_plural = "Speaking Analyses"

    def __str__(self):
        return f"Speaking Analyse - Score: {self.overall_band_score}"


class ReadingAnalyse(BaseModel):
    reading = fields.OneToOneField('models.Reading', related_name='analyse', description="Related reading test")
    correct_answers = fields.IntField(default=0, description="Number of correct answers")
    overall_score = fields.DecimalField(max_digits=3, decimal_places=1, description="Overall score")
    timing = fields.TimeField(description="Time taken")
    feedback = fields.TextField(description="Feedback for the test")

    class Meta:
        table = "reading_analyses"
        verbose_name = "Reading Analyse"
        verbose_name_plural = "Reading Analyses"

    def __str__(self):
        return f"Reading Analyse - Score: {self.overall_score}"


class GrammarAnalyse(BaseModel):
    grammar = fields.OneToOneField('models.Grammar', related_name='analyse', description="Related grammar test")
    correct_answers = fields.IntField(default=0, description="Number of correct answers")
    overall_score = fields.DecimalField(max_digits=3, decimal_places=1, description="Overall score")
    timing = fields.TimeField(description="Time taken")
    feedback = fields.TextField(description="Feedback for the test")

    class Meta:
        table = "grammar_analyses"
        verbose_name = "Grammar Analyse"
        verbose_name_plural = "Grammar Analyses"

    def __str__(self):
        return f"Grammar Analyse - Score: {self.overall_score}"
