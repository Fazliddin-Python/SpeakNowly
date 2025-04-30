from tortoise import fields
from ..base import BaseModel

class Writing(BaseModel):
    status = fields.CharField(max_length=15, default="", null=True)
    user = fields.ForeignKeyField('models.User', related_name='writings')
    start_time = fields.DatetimeField(null=True)
    end_time = fields.DatetimeField(null=True)

    class Meta:
        table = "writings"

class WritingPart1(BaseModel):
    writing = fields.OneToOneField('models.Writing', related_name='part1')
    content = fields.TextField()
    answer = fields.TextField(null=True)
    diagram = fields.CharField(max_length=255, null=True)
    diagram_data = fields.JSONField(null=True)

    class Meta:
        table = "writing_part1"

class WritingPart2(BaseModel):
    writing = fields.OneToOneField('models.Writing', related_name='part2')
    content = fields.TextField()
    answer = fields.TextField(null=True)

    class Meta:
        table = "writing_part2"