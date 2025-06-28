from fastadmin import TortoiseModelAdmin, register, WidgetType
from models import Speaking, SpeakingQuestion, SpeakingAnswer, SpeakingPart, SpeakingStatus


@register(Speaking)
class SpeakingAdmin(TortoiseModelAdmin):
    list_display = ("id", "user", "status", "start_time", "end_time")
    list_filter = ("status",)
    list_select_related = ("user",)

    formfield_overrides = {
        "status": (WidgetType.Select, {
            "options": [
                {"label": s.name.title(), "value": s.value}
                for s in Speaking._meta.fields_map["status"].enum_type
            ]
        }),
        "start_time": (WidgetType.DateTimePicker, {}),
        "end_time": (WidgetType.DateTimePicker, {}),
    }


@register(SpeakingQuestion)
class SpeakingQuestionAdmin(TortoiseModelAdmin):
    list_display = ("id", "speaking", "part", "title")
    list_select_related = ("speaking",)

    formfield_overrides = {
        "part": (WidgetType.Select, {
            "options": [
                {"label": p.name.replace("_", " ").title(), "value": p.value}
                for p in SpeakingQuestion._meta.fields_map["part"].enum_type
            ]
        }),
        "title": (WidgetType.Input, {}),
        "content": (WidgetType.TextArea, {}),
    }

