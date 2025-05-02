from tortoise import fields
from ..base import BaseModel

class Listening(BaseModel):
    status = fields.CharField(max_length=15, default="", null=True, description="Status of the test")
    user = fields.ForeignKeyField('models.User', related_name='listenings', description="Related user")
    start_time = fields.DatetimeField(null=True, description="Start time of the test")
    end_time = fields.DatetimeField(null=True, description="End time of the test")

    class Meta:
        table = "listenings"

class ListeningPart1(BaseModel):
    listening = fields.OneToOneField('models.Listening', related_name='part1', description="Related listening test part 1")
    content = fields.TextField(description="Content of the test")
    answer = fields.TextField(null=True, description="User's answer")
    audio = fields.CharField(max_length=255, null=True, description="Audio file path")

    class Meta:
        table = "listening_part1"

class ListeningPart2(BaseModel):
    listening = fields.OneToOneField('models.Listening', related_name='part2', description="Related listening test part 2")
    content = fields.TextField(description="Content of the test")
    answer = fields.TextField(null=True, description="User's answer")
    audio = fields.CharField(max_length=255, null=True, description="Audio file path")

    class Meta:
        table = "listening_part2"

class ListeningPart3(BaseModel):
    listening = fields.OneToOneField('models.Listening', related_name='part3', description="Related listening test part 3")
    content = fields.TextField(description="Content of the test")
    answer = fields.TextField(null=True, description="User's answer")
    audio = fields.CharField(max_length=255, null=True, description="Audio file path")

    class Meta:
        table = "listening_part3"