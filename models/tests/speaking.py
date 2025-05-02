from tortoise import fields
from ..base import BaseModel

class Speaking(BaseModel):
    status = fields.CharField(max_length=15, default="", null=True, description="Status of the test")
    user = fields.ForeignKeyField('models.User', related_name='speakings', description="Related user")
    start_time = fields.DatetimeField(null=True, description="Start time of the test")
    end_time = fields.DatetimeField(null=True, description="End time of the test")

    class Meta:
        table = "speakings"

class SpeakingPart1(BaseModel):
    speaking = fields.OneToOneField('models.Speaking', related_name='part1', description="Related speaking test part 1")
    content = fields.TextField(description="Content of the test")
    answer = fields.TextField(null=True, description="User's answer")
    audio = fields.CharField(max_length=255, null=True, description="Audio file path")

    class Meta:
        table = "speaking_part1"

class SpeakingPart2(BaseModel):
    speaking = fields.OneToOneField('models.Speaking', related_name='part2', description="Related speaking test part 2")
    content = fields.TextField(description="Content of the test")
    answer = fields.TextField(null=True, description="User's answer")
    audio = fields.CharField(max_length=255, null=True, description="Audio file path")

    class Meta:
        table = "speaking_part2"

class SpeakingPart3(BaseModel):
    speaking = fields.OneToOneField('models.Speaking', related_name='part3', description="Related speaking test part 3")
    content = fields.TextField(description="Content of the test")
    answer = fields.TextField(null=True, description="User's answer")
    audio = fields.CharField(max_length=255, null=True, description="Audio file path")

    class Meta:
        table = "speaking_part3"