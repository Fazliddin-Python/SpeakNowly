from tortoise import fields
from .base import BaseModel

class ListeningAnalyse(BaseModel):
    listening = fields.OneToOneField('models.Listening', related_name='analyse')
    correct_answers = fields.IntField(default=0)
    overall_score = fields.DecimalField(max_digits=3, decimal_places=1)
    timing = fields.TimeField()
    feedback = fields.TextField()

    class Meta:
        table = "listening_analyses"

class WritingAnalyse(BaseModel):
    writing = fields.OneToOneField('models.Writing', related_name='analyse')
    task_achievement_feedback = fields.TextField()
    task_achievement_score = fields.DecimalField(max_digits=3, decimal_places=1)
    lexical_resource_feedback = fields.TextField()
    lexical_resource_score = fields.DecimalField(max_digits=3, decimal_places=1)
    coherence_and_cohesion_feedback = fields.TextField()
    coherence_and_cohesion_score = fields.DecimalField(max_digits=3, decimal_places=1)
    grammatical_range_and_accuracy_feedback = fields.TextField()
    grammatical_range_and_accuracy_score = fields.DecimalField(max_digits=3, decimal_places=1)
    overall_band_score = fields.DecimalField(max_digits=3, decimal_places=1)
    total_feedback = fields.TextField()

    class Meta:
        table = "writing_analyses"

class SpeakingAnalyse(BaseModel):
    speaking = fields.OneToOneField('models.Speaking', related_name='analyse')
    fluency_and_coherence_feedback = fields.TextField()
    fluency_and_coherence_score = fields.DecimalField(max_digits=3, decimal_places=1)
    lexical_resource_feedback = fields.TextField()
    lexical_resource_score = fields.DecimalField(max_digits=3, decimal_places=1)
    grammatical_range_and_accuracy_feedback = fields.TextField()
    grammatical_range_and_accuracy_score = fields.DecimalField(max_digits=3, decimal_places=1)
    pronunciation_feedback = fields.TextField()
    pronunciation_score = fields.DecimalField(max_digits=3, decimal_places=1)
    overall_band_score = fields.DecimalField(max_digits=3, decimal_places=1)
    total_feedback = fields.TextField()

    class Meta:
        table = "speaking_analyses"

class ReadingAnalyse(BaseModel):
    reading = fields.OneToOneField('models.Reading', related_name='analyse')
    correct_answers = fields.IntField(default=0)
    overall_score = fields.DecimalField(max_digits=3, decimal_places=1)
    timing = fields.TimeField()
    feedback = fields.TextField()

    class Meta:
        table = "reading_analyses"

class GrammarAnalyse(BaseModel):
    grammar = fields.OneToOneField('models.Grammar', related_name='analyse')
    correct_answers = fields.IntField(default=0)
    overall_score = fields.DecimalField(max_digits=3, decimal_places=1)
    timing = fields.TimeField()
    feedback = fields.TextField()

    class Meta:
        table = "grammar_analyses"

class VocabularyAnalyse(BaseModel):
    vocabulary = fields.OneToOneField('models.Vocabulary', related_name='analyse')
    correct_answers = fields.IntField(default=0)
    overall_score = fields.DecimalField(max_digits=3, decimal_places=1)
    timing = fields.TimeField()
    feedback = fields.TextField()

    class Meta:
        table = "vocabulary_analyses"

class PronunciationAnalyse(BaseModel):
    pronunciation = fields.OneToOneField('models.Pronunciation', related_name='analyse')
    correct_answers = fields.IntField(default=0)
    overall_score = fields.DecimalField(max_digits=3, decimal_places=1)
    timing = fields.TimeField()
    feedback = fields.TextField()

    class Meta:
        table = "pronunciation_analyses"