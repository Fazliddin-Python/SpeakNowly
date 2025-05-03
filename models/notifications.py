from tortoise import fields
from .base import BaseModel
from gettext import gettext as _

class Message(BaseModel):
    MAIL = "mail"
    SITE = "site"
    MAIL_SITE = "mail_site"

    MESSAGE_TYPES = (
        (MAIL, "Mail"),
        (SITE, "Site"),
        (MAIL_SITE, "Mail and Site"),
    )

    user = fields.ForeignKeyField("models.User", related_name="messages", null=True, description="User")
    type = fields.CharField(max_length=20, choices=MESSAGE_TYPES, default=SITE, description="Type")
    title = fields.CharField(max_length=255, description="Title")
    description = fields.TextField(null=True, description="Description")
    content = fields.TextField(description="Content")

    class Meta:
        table = "messages"
        verbose_name = "Message"
        verbose_name_plural = "Messages"

class ReadStatus(BaseModel):
    message = fields.ForeignKeyField("models.Message", related_name="read_statuses", description="Message")
    user = fields.ForeignKeyField("models.User", related_name="read_statuses", description="User")
    read_at = fields.DatetimeField(null=True, description="Read at")

    class Meta:
        table = "read_statuses"
        verbose_name = "Read Status"
        verbose_name_plural = "Read Statuses"
