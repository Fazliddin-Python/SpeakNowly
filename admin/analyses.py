from fastadmin import TortoiseModelAdmin, register, WidgetType
from models.analyses import ListeningAnalyse, WritingAnalyse, SpeakingAnalyse, ReadingAnalyse
from models import User, ReadingPassage, Writing, Speaking, ListeningSession


@register(ListeningAnalyse)
class ListeningAnalyseAdmin(TortoiseModelAdmin):
    list_display = (
        "id", "user", "session", "correct_answers",
        "overall_score", "status", "duration", "created_at",
    )
    list_filter = ("status",)
    list_select_related = ("user", "session")
    search_fields = ("status",)

    formfield_overrides = {
        "correct_answers": (WidgetType.InputNumber, {}),
        "overall_score":   (WidgetType.InputNumber, {"step": 0.1}),
        "status":          (WidgetType.Input, {}),
        "duration":        (WidgetType.TimePicker, {}),
    }

    async def get_formfield_override(self, field_name: str):
        if field_name == "user":
            users = await User.all().values("id", "email")
            return (WidgetType.Select, {"options": [{"label": u["email"], "value": u["id"]} for u in users]})
        if field_name == "session":
            sessions = await ListeningSession.all().values("id")
            return (WidgetType.Select, {"options": [{"label": f"Session {s['id']}", "value": s["id"]} for s in sessions]})
        return await super().get_formfield_override(field_name)


@register(WritingAnalyse)
class WritingAnalyseAdmin(TortoiseModelAdmin):
    list_display = (
        "id", "writing", "overall_band_score", "duration", "created_at",
    )

    formfield_overrides = {
        "task_achievement_score":               (WidgetType.InputNumber, {"step": 0.1}),
        "lexical_resource_score":              (WidgetType.InputNumber, {"step": 0.1}),
        "coherence_and_cohesion_score":        (WidgetType.InputNumber, {"step": 0.1}),
        "grammatical_range_and_accuracy_score":(WidgetType.InputNumber, {"step": 0.1}),
        "word_count_score":                    (WidgetType.InputNumber, {"step": 0.1}),
        "overall_band_score":                  (WidgetType.InputNumber, {"step": 0.1}),
        "duration":                            (WidgetType.TimePicker, {}),
    }

    async def get_formfield_override(self, field_name: str):
        if field_name == "writing":
            writings = await Writing.all().values("id")
            return (WidgetType.Select, {"options": [{"label": f"Writing {w['id']}", "value": w["id"]} for w in writings]})
        return await super().get_formfield_override(field_name)


@register(SpeakingAnalyse)
class SpeakingAnalyseAdmin(TortoiseModelAdmin):
    list_display = (
        "id", "speaking", "overall_band_score", "duration", "created_at",
    )

    formfield_overrides = {
        "fluency_and_coherence_score":         (WidgetType.InputNumber, {"step": 0.1}),
        "lexical_resource_score":              (WidgetType.InputNumber, {"step": 0.1}),
        "grammatical_range_and_accuracy_score":(WidgetType.InputNumber, {"step": 0.1}),
        "pronunciation_score":                 (WidgetType.InputNumber, {"step": 0.1}),
        "overall_band_score":                  (WidgetType.InputNumber, {"step": 0.1}),
        "duration":                            (WidgetType.TimePicker, {}),
    }

    async def get_formfield_override(self, field_name: str):
        if field_name == "speaking":
            speakings = await Speaking.all().values("id")
            return (WidgetType.Select, {"options": [{"label": f"Speaking {s['id']}", "value": s["id"]} for s in speakings]})
        return await super().get_formfield_override(field_name)


@register(ReadingAnalyse)
class ReadingAnalyseAdmin(TortoiseModelAdmin):
    list_display = (
        "id", "user", "passage", "correct_answers",
        "overall_score", "duration", "created_at",
    )
    list_select_related = ("user", "passage")
    search_fields = ()

    formfield_overrides = {
        "correct_answers": (WidgetType.InputNumber, {}),
        "overall_score":   (WidgetType.InputNumber, {"step": 0.1}),
        "duration":        (WidgetType.TimePicker, {}),
    }

    async def get_formfield_override(self, field_name: str):
        if field_name == "user":
            users = await User.all().values("id", "email")
            return (WidgetType.Select, {"options": [{"label": u["email"], "value": u["id"]} for u in users]})
        if field_name == "passage":
            passages = await ReadingPassage.all().values("id", "title")
            return (WidgetType.Select, {"options": [{"label": p["title"], "value": p["id"]} for p in passages]})
        return await super().get_formfield_override(field_name)
