from fastadmin import TortoiseModelAdmin, register, WidgetType
from models import Writing, WritingPart1, WritingPart2, WritingStatus


@register(Writing)
class WritingAdmin(TortoiseModelAdmin):
    list_display = ("id", "user", "status", "start_time", "end_time")
    list_filter = ("status",)
    list_select_related = ("user",)

    formfield_overrides = {
        "status": (WidgetType.Select, {
            "options": [
                {"label": s.name.title(), "value": s.value}
                for s in Writing._meta.fields_map["status"].enum_type
            ]
        }),
        "start_time": (WidgetType.DateTimePicker, {}),
        "end_time": (WidgetType.DateTimePicker, {}),
    }


@register(WritingPart1)
class WritingPart1Admin(TortoiseModelAdmin):
    list_display = ("id", "writing",)
    list_select_related = ("writing",)

    formfield_overrides = {
        "content": (WidgetType.TextArea, {}),
        "diagram": (WidgetType.Input, {}),
        "diagram_data": (WidgetType.TextArea, {}),
        "answer": (WidgetType.TextArea, {}),
    }


@register(WritingPart2)
class WritingPart2Admin(TortoiseModelAdmin):
    list_display = ("id", "writing",)
    list_select_related = ("writing",)

    formfield_overrides = {
        "content": (WidgetType.TextArea, {}),
        "answer": (WidgetType.TextArea, {}),
    }
