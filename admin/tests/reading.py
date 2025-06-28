from fastadmin import TortoiseModelAdmin, register, WidgetType
from models import (
    User, Reading, ReadingPassage, ReadingQuestion, ReadingAnswer, ReadingVariant
)
from models.tests.constants import Constants


@register(ReadingPassage)
class ReadingPassageAdmin(TortoiseModelAdmin):
    list_display = ("id", "title", "level", "number")
    search_fields = ("title",)

    formfield_overrides = {
        "title": (WidgetType.Input, {}),
        "text": (WidgetType.TextArea, {}),
        "skills": (WidgetType.TextArea, {}),
        "level": (WidgetType.Select, {
            "options": [{"label": l.name.title(), "value": l.value} for l in Constants.PassageLevel]
        }),
    }


@register(ReadingQuestion)
class ReadingQuestionAdmin(TortoiseModelAdmin):
    list_display = ("id", "passage", "text", "type", "score")
    list_select_related = ("passage",)

    formfield_overrides = {
        "text": (WidgetType.TextArea, {}),
        "score": (WidgetType.InputNumber, {}),
        "type": (WidgetType.Select, {
            "options": [{"label": t.name.replace("_", " ").title(), "value": t.value} for t in Constants.QuestionType]
        })
    }

    async def get_formfield_override(self, field_name: str):
        if field_name == "passage":
            passages = await ReadingPassage.all().values("id", "title")
            return WidgetType.Select, {
                "options": [{"label": p["title"], "value": p["id"]} for p in passages]
            }
        return await super().get_formfield_override(field_name)


@register(ReadingVariant)
class ReadingVariantAdmin(TortoiseModelAdmin):
    list_display = ("id", "question", "text", "is_correct")
    list_select_related = ("question",)

    formfield_overrides = {
        "text": (WidgetType.TextArea, {}),
        "is_correct": (WidgetType.Switch, {}),
    }

    async def get_formfield_override(self, field_name: str):
        if field_name == "question":
            questions = await ReadingQuestion.all().values("id")
            return WidgetType.Select, {
                "options": [{"label": f"Question {q['id']}", "value": q["id"]} for q in questions]
            }
        return await super().get_formfield_override(field_name)


@register(Reading)
class ReadingAdmin(TortoiseModelAdmin):
    list_display = ("id", "user", "status", "score", "start_time", "end_time")
    list_filter = ("status",)
    list_select_related = ("user",)

    formfield_overrides = {
        "start_time": (WidgetType.DateTimePicker, {}),
        "end_time": (WidgetType.DateTimePicker, {}),
        "duration": (WidgetType.InputNumber, {}),
        "score": (WidgetType.InputNumber, {"step": 0.1}),
        "status": (WidgetType.Select, {
            "options": [{"label": s.name.title(), "value": s.value} for s in Constants.ReadingStatus]
        })
    }

    async def get_formfield_override(self, field_name: str):
        if field_name == "user":
            users = await User.all().values("id", "email")
            return WidgetType.Select, {
                "options": [{"label": u["email"], "value": u["id"]} for u in users]
            }
        if field_name == "passages":
            passages = await ReadingPassage.all().values("id", "title")
            return WidgetType.SelectMultiple, {
                "options": [{"label": p["title"], "value": p["id"]} for p in passages]
            }
        return await super().get_formfield_override(field_name)


@register(ReadingAnswer)
class ReadingAnswerAdmin(TortoiseModelAdmin):
    list_display = ("id", "user", "reading", "question", "variant", "is_correct")
    list_select_related = ("user", "reading", "question", "variant")

    formfield_overrides = {
        "status": (WidgetType.Select, {
            "options": [
                {"label": "Answered", "value": "answered"},
                {"label": "Not Answered", "value": "not_answered"}
            ]
        }),
        "text": (WidgetType.TextArea, {}),
        "explanation": (WidgetType.TextArea, {}),
        "correct_answer": (WidgetType.TextArea, {}),
        "is_correct": (WidgetType.Switch, {}),
    }

    async def get_formfield_override(self, field_name: str):
        if field_name == "user":
            users = await User.all().values("id", "email")
            return WidgetType.Select, {
                "options": [{"label": u["email"], "value": u["id"]} for u in users]
            }
        if field_name == "reading":
            readings = await Reading.all().values("id")
            return WidgetType.Select, {
                "options": [{"label": f"Reading {r['id']}", "value": r["id"]} for r in readings]
            }
        if field_name == "question":
            questions = await ReadingQuestion.all().values("id")
            return WidgetType.Select, {
                "options": [{"label": f"Question {q['id']}", "value": q["id"]} for q in questions]
            }
        if field_name == "variant":
            variants = await ReadingVariant.all().values("id")
            return WidgetType.Select, {
                "options": [{"label": f"Variant {v['id']}", "value": v["id"]} for v in variants]
            }
        return await super().get_formfield_override(field_name)
