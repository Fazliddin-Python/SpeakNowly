from tortoise import fields
from .base import BaseModel

class Comment(BaseModel):
    ACTIVE = "active"
    INACTIVE = "inactive"

    STATUS = [
        (ACTIVE, "Active"),
        (INACTIVE, "Inactive"),
    ]

    text = fields.TextField(description="Comment text")
    user = fields.ForeignKeyField("models.User", related_name="comments", description="User")
    rate = fields.FloatField(default=0, description="Rating")
    status = fields.CharField(max_length=255, choices=STATUS, default=ACTIVE, description="Status")

    class Meta:
        table = "comments"
        verbose_name = "Comment"
        verbose_name_plural = "Comments"