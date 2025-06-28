from fastadmin import TortoiseModelAdmin, register, WidgetType
from models.comments import Comment, CommentStatus
from models import User

@register(Comment)
class CommentAdmin(TortoiseModelAdmin):
    list_display = (
        "id", "user", "rate", "status", "text", "created_at",
    )
    list_filter = ("status",)
    search_fields = ("text",)

    list_select_related = ("user",)

    formfield_overrides = {
        "text":   (WidgetType.TextArea, {}),
        "rate":   (WidgetType.InputNumber, {"min": 1, "max": 5, "step": 0.5}),
        "status": (WidgetType.Select, {
            "options": [
                {"label": "Active", "value": CommentStatus.ACTIVE.value},
                {"label": "Inactive", "value": CommentStatus.INACTIVE.value},
            ]
        }),
    }

    async def get_formfield_override(self, field_name: str):
        if field_name == "user":
            users = await User.all().values("id", "email")
            return (WidgetType.Select, {"options": [{"label": u["email"], "value": u["id"]} for u in users]})
        return await super().get_formfield_override(field_name)
