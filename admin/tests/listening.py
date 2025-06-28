from fastadmin import TortoiseModelAdmin, register, WidgetType
from models import (
    Listening, ListeningPart, ListeningSection,
    ListeningQuestion, ListeningSession, ListeningAnswer, User,
    ListeningQuestionType, ListeningPartNumber, ListeningSessionStatus
)


@register(Listening)
class ListeningAdmin(TortoiseModelAdmin):
    list_display = ("id", "title", "created_at")
    search_fields = ("title",)
    formfield_overrides = {
        "title": (WidgetType.Input, {}),
        "description": (WidgetType.TextArea, {}),
    }


@register(ListeningPart)
class ListeningPartAdmin(TortoiseModelAdmin):
    list_display = ("id", "listening", "part_number", "audio_file", "created_at")
    list_select_related = ("listening",)

    formfield_overrides = {
        "audio_file": (WidgetType.Upload, {
            "accept": [".mp3", ".wav"],
            "upload_url": "/admin/api/upload-audio/",
            "display_url_prefix": "/media/audio/"
        }),
        "part_number": (WidgetType.Select, {
            "options": [{"label": f"Part {p.name[-1]}", "value": p.value} for p in ListeningPartNumber]
        }),
    }

    async def get_formfield_override(self, field_name: str):
        if field_name == "listening":
            items = await Listening.all().values("id", "title")
            return WidgetType.Select, {
                "options": [{"label": i["title"], "value": i["id"]} for i in items]
            }
        return await super().get_formfield_override(field_name)


@register(ListeningSection)
class ListeningSectionAdmin(TortoiseModelAdmin):
    list_display = ("id", "part", "section_number", "question_type", "start_index", "end_index")
    list_select_related = ("part",)

    formfield_overrides = {
        "section_number": (WidgetType.InputNumber, {}),
        "start_index": (WidgetType.InputNumber, {}),
        "end_index": (WidgetType.InputNumber, {}),
        "question_text": (WidgetType.TextArea, {}),
        "options": (WidgetType.TextArea, {}),
        "question_type": (WidgetType.Select, {
            "options": [{"label": t.name.replace("_", " ").title(), "value": t.value} for t in ListeningQuestionType]
        }),
    }

    async def get_formfield_override(self, field_name: str):
        if field_name == "part":
            parts = await ListeningPart.all().values("id")
            return WidgetType.Select, {
                "options": [{"label": f"Part {p['id']}", "value": p["id"]} for p in parts]
            }
        return await super().get_formfield_override(field_name)


@register(ListeningQuestion)
class ListeningQuestionAdmin(TortoiseModelAdmin):
    list_display = ("id", "section", "index", "created_at")
    list_select_related = ("section",)

    formfield_overrides = {
        "index": (WidgetType.InputNumber, {}),
        "question_text": (WidgetType.TextArea, {}),
        "options": (WidgetType.TextArea, {}),
        "correct_answer": (WidgetType.TextArea, {}),
    }

    async def get_formfield_override(self, field_name: str):
        if field_name == "section":
            sections = await ListeningSection.all().values("id")
            return WidgetType.Select, {
                "options": [{"label": f"Section {s['id']}", "value": s["id"]} for s in sections]
            }
        return await super().get_formfield_override(field_name)


@register(ListeningSession)
class ListeningSessionAdmin(TortoiseModelAdmin):
    list_display = ("id", "user", "exam", "status", "start_time", "end_time")
    list_filter = ("status",)
    list_select_related = ("user", "exam")
    search_fields = ("user.email",)

    formfield_overrides = {
        "start_time": (WidgetType.DateTimePicker, {}),
        "end_time": (WidgetType.DateTimePicker, {}),
        "status": (WidgetType.Select, {
            "options": [{"label": s.name.title(), "value": s.value} for s in ListeningSessionStatus]
        }),
    }

    async def get_formfield_override(self, field_name: str):
        if field_name == "user":
            users = await User.all().values("id", "email")
            return WidgetType.Select, {
                "options": [{"label": u["email"], "value": u["id"]} for u in users]
            }
        if field_name == "exam":
            exams = await Listening.all().values("id", "title")
            return WidgetType.Select, {
                "options": [{"label": e["title"], "value": e["id"]} for e in exams]
            }
        return await super().get_formfield_override(field_name)


@register(ListeningAnswer)
class ListeningAnswerAdmin(TortoiseModelAdmin):
    list_display = ("id", "session", "question", "user", "is_correct", "score")
    list_select_related = ("session", "user", "question")
    search_fields = ("user.email",)

    formfield_overrides = {
        "user_answer": (WidgetType.TextArea, {}),
        "is_correct": (WidgetType.Switch, {}),
        "score": (WidgetType.InputNumber, {"step": 0.1}),
    }

    async def get_formfield_override(self, field_name: str):
        if field_name == "user":
            users = await User.all().values("id", "email")
            return WidgetType.Select, {
                "options": [{"label": u["email"], "value": u["id"]} for u in users]
            }
        if field_name == "session":
            sessions = await ListeningSession.all().values("id")
            return WidgetType.Select, {
                "options": [{"label": f"Session {s['id']}", "value": s["id"]} for s in sessions]
            }
        if field_name == "question":
            questions = await ListeningQuestion.all().values("id")
            return WidgetType.Select, {
                "options": [{"label": f"Question {q['id']}", "value": q["id"]} for q in questions]
            }
        return await super().get_formfield_override(field_name)
