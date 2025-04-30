from tortoise import fields
from ..base import BaseModel

class Listening(BaseModel):
    status = fields.CharField(max_length=15, default="", null=True)
    user = fields.ForeignKeyField('models.User', related_name='listenings')
    start_time = fields.DatetimeField(null=True)
    end_time = fields.DatetimeField(null=True)

    class Meta:
        table = "listenings"

class ListeningPart1(BaseModel):
    listening = fields.OneToOneField('models.Listening', related_name='part1')
    content = fields.TextField()
    answer = fields.TextField(null=True)
    audio = fields.CharField(max_length=255, null=True)

    class Meta:
        table = "listening_part1"

class ListeningPart2(BaseModel):
    listening = fields.OneToOneField('models.Listening', related_name='part2')
    content = fields.TextField()
    answer = fields.TextField(null=True)
    audio = fields.CharField(max_length=255, null=True)

    class Meta:
        table = "listening_part2"

class ListeningPart3(BaseModel):
    listening = fields.OneToOneField('models.Listening', related_name='part3')
    content = fields.TextField()
    answer = fields.TextField(null=True)
    audio = fields.CharField(max_length=255, null=True)

    class Meta:
        table = "listening_part3"