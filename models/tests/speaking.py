from tortoise import fields
from ..base import BaseModel

class Speaking(BaseModel):
    status = fields.CharField(max_length=15, default="", null=True)
    user = fields.ForeignKeyField('models.User', related_name='speakings')
    start_time = fields.DatetimeField(null=True)
    end_time = fields.DatetimeField(null=True)

    class Meta:
        table = "speakings"

class SpeakingPart1(BaseModel):
    speaking = fields.OneToOneField('models.Speaking', related_name='part1')
    content = fields.TextField()
    answer = fields.TextField(null=True)
    audio = fields.CharField(max_length=255, null=True)

    class Meta:
        table = "speaking_part1"

class SpeakingPart2(BaseModel):
    speaking = fields.OneToOneField('models.Speaking', related_name='part2')
    content = fields.TextField()
    answer = fields.TextField(null=True)
    audio = fields.CharField(max_length=255, null=True)

    class Meta:
        table = "speaking_part2"

class SpeakingPart3(BaseModel):
    speaking = fields.OneToOneField('models.Speaking', related_name='part3')
    content = fields.TextField()
    answer = fields.TextField(null=True)
    audio = fields.CharField(max_length=255, null=True)

    class Meta:
        table = "speaking_part3"