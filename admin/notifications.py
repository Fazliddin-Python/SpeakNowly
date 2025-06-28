from fastadmin import TortoiseModelAdmin, register, WidgetType
from models.notifications import Message, ReadStatus, MessageType
from models import User


@register(Message)
class MessageAdmin(TortoiseModelAdmin):
    list_display = (
        "id", "user", "type", "title", "created_at",
    )
    list_filter = ("type",)
    list_select_related = ("user",)
    search_fields = ("title",)

    formfield_overrides = {
        "type": (WidgetType.Select, {
            "options": [
                {"label": "Mail", "value": MessageType.MAIL.value},
                {"label": "Site", "value": MessageType.SITE.value},
                {"label": "Mail & Site", "value": MessageType.MAIL_SITE.value},
            ]
        }),
        "title":       (WidgetType.Input, {}),
        "description": (WidgetType.TextArea, {}),
        "content":     (WidgetType.TextArea, {}),
    }

    async def get_formfield_override(self, field_name: str):
        if field_name == "user":
            users = await User.all().values("id", "email")
            return (WidgetType.Select, {"options": [{"label": u["email"], "value": u["id"]} for u in users]})
        return await super().get_formfield_override(field_name)

    async def create_object(self, data: dict) -> Message:
        data.pop("id", None)
        message = await super().create_object(data)

        try:
            if message.type in (MessageType.MAIL, MessageType.MAIL_SITE) and message.user and message.user.email:
                subject = message.title or "New Message from SpeakNowly"
                html_body = f"""
                <p>Hi {message.user.first_name or 'there'},</p>
                <p>{message.description or ''}</p>
                <p>{message.content or ''}</p>
                """
                from services.users.email_service import EmailService
                await EmailService.send_email(
                    subject=subject,
                    recipients=[message.user.email],
                    html_body=html_body,
                )
        except Exception as e:
            print("❌ Ошибка при отправке email:", e)

        return message


@register(ReadStatus)
class ReadStatusAdmin(TortoiseModelAdmin):
    list_display = (
        "id", "user", "message", "read_at",
    )
    list_select_related = ("user", "message")
    search_fields = ()

    formfield_overrides = {
        "read_at": (WidgetType.DateTimePicker, {}),
    }

    async def get_formfield_override(self, field_name: str):
        if field_name == "user":
            users = await User.all().values("id", "email")
            return (WidgetType.Select, {"options": [{"label": u["email"], "value": u["id"]} for u in users]})
        if field_name == "message":
            messages = await Message.all().values("id", "title")
            return (WidgetType.Select, {"options": [{"label": m["title"], "value": m["id"]} for m in messages]})
        return await super().get_formfield_override(field_name)
