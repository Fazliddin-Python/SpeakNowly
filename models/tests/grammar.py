from tortoise import fields
from ..base import BaseModel

class Grammar(BaseModel):
    status = fields.CharField(max_length=15, default="", null=True)
    user = fields.ForeignKeyField('models.User', related_name='grammars')
    start_time = fields.DatetimeField(null=True)
    end_time = fields.DatetimeField(null=True)

    class Meta:
        table = "grammars"

class GrammarPart1(BaseModel):
    grammar = fields.OneToOneField('models.Grammar', related_name='part1')
    content = fields.TextField()
    answer = fields.TextField(null=True)

    class Meta:
        table = "grammar_part1"

class GrammarPart2(BaseModel):
    grammar = fields.OneToOneField('models.Grammar', related_name='part2')
    content = fields.TextField()
    answer = fields.TextField(null=True)

    class Meta:
        table = "grammar_part2"

class GrammarPart3(BaseModel):
    grammar = fields.OneToOneField('models.Grammar', related_name='part3')
    content = fields.TextField()
    answer = fields.TextField(null=True)

    class Meta:
        table = "grammar_part3"