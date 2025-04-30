from tortoise import fields
from ..base import BaseModel

class Vocabulary(BaseModel):
    status = fields.CharField(max_length=15, default="", null=True)
    user = fields.ForeignKeyField('models.User', related_name='vocabularies')
    start_time = fields.DatetimeField(null=True)
    end_time = fields.DatetimeField(null=True)

    class Meta:
        table = "vocabularies"

class VocabularyPart1(BaseModel):
    vocabulary = fields.OneToOneField('models.Vocabulary', related_name='part1')
    content = fields.TextField()
    answer = fields.TextField(null=True)

    class Meta:
        table = "vocabulary_part1"

class VocabularyPart2(BaseModel):
    vocabulary = fields.OneToOneField('models.Vocabulary', related_name='part2')
    content = fields.TextField()
    answer = fields.TextField(null=True)

    class Meta:
        table = "vocabulary_part2"

class VocabularyPart3(BaseModel):
    vocabulary = fields.OneToOneField('models.Vocabulary', related_name='part3')
    content = fields.TextField()
    answer = fields.TextField(null=True)

    class Meta:
        table = "vocabulary_part3"