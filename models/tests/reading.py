from tortoise import fields
from ..base import BaseModel

class Reading(BaseModel):
    status = fields.CharField(max_length=15, default="", null=True)
    user = fields.ForeignKeyField('models.User', related_name='readings')
    start_time = fields.DatetimeField(null=True)
    end_time = fields.DatetimeField(null=True)

    class Meta:
        table = "readings"

class ReadingPart1(BaseModel):
    reading = fields.OneToOneField('models.Reading', related_name='part1')
    content = fields.TextField()
    answer = fields.TextField(null=True)

    class Meta:
        table = "reading_part1"

class ReadingPart2(BaseModel):
    reading = fields.OneToOneField('models.Reading', related_name='part2')
    content = fields.TextField()
    answer = fields.TextField(null=True)

    class Meta:
        table = "reading_part2"

class ReadingPart3(BaseModel):
    reading = fields.OneToOneField('models.Reading', related_name='part3')
    content = fields.TextField()
    answer = fields.TextField(null=True)

    class Meta:
        table = "reading_part3"