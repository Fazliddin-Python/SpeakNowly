from tortoise import fields
from ..base import BaseModel

class Pronunciation(BaseModel):
    status = fields.CharField(max_length=15, default="", null=True)
    user = fields.ForeignKeyField('models.User', related_name='pronunciations')
    start_time = fields.DatetimeField(null=True)
    end_time = fields.DatetimeField(null=True)

    class Meta:
        table = "pronunciations"

class PronunciationPart1(BaseModel):
    pronunciation = fields.OneToOneField('models.Pronunciation', related_name='part1')
    content = fields.TextField()
    answer = fields.TextField(null=True)
    audio = fields.CharField(max_length=255, null=True)

    class Meta:
        table = "pronunciation_part1"

class PronunciationPart2(BaseModel):
    pronunciation = fields.OneToOneField('models.Pronunciation', related_name='part2')
    content = fields.TextField()
    answer = fields.TextField(null=True)
    audio = fields.CharField(max_length=255, null=True)

    class Meta:
        table = "pronunciation_part2"

class PronunciationPart3(BaseModel):
    pronunciation = fields.OneToOneField('models.Pronunciation', related_name='part3')
    content = fields.TextField()
    answer = fields.TextField(null=True)
    audio = fields.CharField(max_length=255, null=True)

    class Meta:
        table = "pronunciation_part3"