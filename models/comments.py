from tortoise import fields
from .base import BaseModel
from enum import Enum

class CommentStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"

class Comment(BaseModel):
    text = fields.TextField(description="Comment text")
    user = fields.ForeignKeyField("models.User", related_name="comments", description="User")
    rate = fields.FloatField(default=0, description="Rating")
    status = fields.CharEnumField(CommentStatus, default=CommentStatus.ACTIVE, description="Status")

    class Meta:
        table = "comments"
        verbose_name = "Comment"
        verbose_name_plural = "Comments"