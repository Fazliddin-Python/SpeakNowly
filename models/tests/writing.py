from tortoise import fields
from ..base import BaseModel

class Writing(BaseModel):
    status = fields.CharField(max_length=15, default="", null=True, description="Status of the test")
    user = fields.ForeignKeyField('models.User', related_name='writings', description="Related user")
    start_time = fields.DatetimeField(null=True, description="Start time of the test")
    end_time = fields.DatetimeField(null=True, description="End time of the test")

    class Meta:
        table = "writings"

class WritingPart1(BaseModel):
    writing = fields.OneToOneField('models.Writing', related_name='part1', description="Related writing test part 1")
    content = fields.TextField(description="Content of the test")
    answer = fields.TextField(null=True, description="User's answer")
    diagram = fields.CharField(max_length=255, null=True, description="Diagram file path")
    diagram_data = fields.JSONField(null=True, description="Data for the diagram")

    class Meta:
        table = "writing_part1"

class WritingPart2(BaseModel):
    writing = fields.OneToOneField('models.Writing', related_name='part2', description="Related writing test part 2")
    content = fields.TextField(description="Content of the test")
    answer = fields.TextField(null=True, description="User's answer")

    class Meta:
        table = "writing_part2"