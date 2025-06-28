from fastadmin import TortoiseModelAdmin, register, WidgetType
from models import TestType


@register(TestType)
class TestTypeAdmin(TortoiseModelAdmin):
    list_display = ("id", "type", "price", "trial_price")

    formfield_overrides = {
        "type": (WidgetType.Select, {
            "options": [
                {"label": t.name.replace("_ENG", "").title(), "value": t.value}
                for t in TestType._meta.fields_map["type"].enum_type
            ]
        }),
        "price": (WidgetType.InputNumber, {}),
        "trial_price": (WidgetType.InputNumber, {}),
    }