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

    user = fields.ForeignKeyField("models.User", related_name="messages", null=True, description=_("User"))
    type = fields.CharField(max_length=20, choices=MESSAGE_TYPES, default=SITE, description=_("Type"))
    title = fields.CharField(max_length=255, description=_("Title"))
    description = fields.TextField(null=True, description=_("Description"))
    content = fields.TextField(description=_("Content"))

    class Meta:
        table = "messages"

class ReadStatus(BaseModel):
    message = fields.ForeignKeyField("models.Message", related_name="read_statuses", null=True, description=_("Message"))
    user = fields.ForeignKeyField("models.User", related_name="read_statuses", description=_("User"))
    read_at = fields.DatetimeField(null=True, description=_("Read at"))

    class Meta:
        table = "read_statuses"