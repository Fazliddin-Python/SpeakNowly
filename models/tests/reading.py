from tortoise import fields
from ..base import BaseModel

class Reading(BaseModel):
    status = fields.CharField(max_length=15, default="", null=True, description="Status of the test")
    user = fields.ForeignKeyField('models.User', related_name='readings', description="Related user")
    start_time = fields.DatetimeField(null=True, description="Start time of the test")
    end_time = fields.DatetimeField(null=True, description="End time of the test")

    class Meta:
        table = "readings"

class ReadingPart1(BaseModel):
    reading = fields.OneToOneField('models.Reading', related_name='part1', description="Related reading test part 1")
    content = fields.TextField(description="Content of the test")
    answer = fields.TextField(null=True, description="User's answer")

    class Meta:
        table = "reading_part1"

class ReadingPart2(BaseModel):
    reading = fields.OneToOneField('models.Reading', related_name='part2', description="Related reading test part 2")
    content = fields.TextField(description="Content of the test")
    answer = fields.TextField(null=True, description="User's answer")

    class Meta:
        table = "reading_part2"

class ReadingPart3(BaseModel):
    reading = fields.OneToOneField('models.Reading', related_name='part3', description="Related reading test part 3")
    content = fields.TextField(description="Content of the test")
    answer = fields.TextField(null=True, description="User's answer")

    class Meta:
        table = "reading_part3"