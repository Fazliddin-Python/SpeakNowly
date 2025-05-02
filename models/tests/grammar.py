from tortoise import fields
from ..base import BaseModel

class Grammar(BaseModel):
    status = fields.CharField(max_length=15, default="", null=True, description="Status of the test")
    user = fields.ForeignKeyField('models.User', related_name='grammars', description="Related user")
    start_time = fields.DatetimeField(null=True, description="Start time of the test")
    end_time = fields.DatetimeField(null=True, description="End time of the test")

    class Meta:
        table = "grammars"

class GrammarPart1(BaseModel):
    grammar = fields.OneToOneField('models.Grammar', related_name='part1', description="Related grammar test part 1")
    content = fields.TextField(description="Content of the test")
    answer = fields.TextField(null=True, description="User's answer")

    class Meta:
        table = "grammar_part1"

class GrammarPart2(BaseModel):
    grammar = fields.OneToOneField('models.Grammar', related_name='part2', description="Related grammar test part 2")
    content = fields.TextField(description="Content of the test")
    answer = fields.TextField(null=True, description="User's answer")

    class Meta:
        table = "grammar_part2"

class GrammarPart3(BaseModel):
    grammar = fields.OneToOneField('models.Grammar', related_name='part3', description="Related grammar test part 3")
    content = fields.TextField(description="Content of the test")
    answer = fields.TextField(null=True, description="User's answer")

    class Meta:
        table = "grammar_part3"