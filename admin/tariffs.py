from fastadmin import TortoiseModelAdmin, register, fastapi_app as admin_app, WidgetType
from models.tariffs import TariffCategory, Tariff, Feature, TariffFeature, Sale


@register(TariffCategory)
class TariffCategoryAdmin(TortoiseModelAdmin):
    list_display = (
        "id", "name", "name_uz", "name_ru", "name_en",
        "sale", "is_active", "created_at",
    )
    list_filter = ("is_active",)
    search_fields = ("name", "name_uz", "name_ru", "name_en")

    formfield_overrides = {
        "name":      (WidgetType.Input, {}),
        "name_uz":   (WidgetType.Input, {}),
        "name_ru":   (WidgetType.Input, {}),
        "name_en":   (WidgetType.Input, {}),
        "sale":      (WidgetType.InputNumber, {}),
        "is_active": (WidgetType.Switch, {}),
    }


@register(Tariff)
class TariffAdmin(TortoiseModelAdmin):
    list_display = (
        "id", "category", "name", "name_uz", "name_ru", "name_en",
        "old_price", "price", "price_in_stars", "tokens", "duration",
        "is_active", "is_default", "created_at",
    )
    list_filter = ("is_active", "is_default")
    search_fields = ("name", "name_uz", "name_ru", "name_en")
    list_select_related = ("category",)

    formfield_overrides = {
        "name":           (WidgetType.Input, {}),
        "name_uz":        (WidgetType.Input, {}),
        "name_ru":        (WidgetType.Input, {}),
        "name_en":        (WidgetType.Input, {}),
        "old_price":      (WidgetType.InputNumber, {}),
        "price":          (WidgetType.InputNumber, {}),
        "price_in_stars": (WidgetType.InputNumber, {}),
        "description":    (WidgetType.TextArea, {}),
        "description_uz": (WidgetType.TextArea, {}),
        "description_ru": (WidgetType.TextArea, {}),
        "description_en": (WidgetType.TextArea, {}),
        "tokens":         (WidgetType.InputNumber, {}),
        "duration":       (WidgetType.InputNumber, {}),
        "is_active":      (WidgetType.Switch, {}),
        "is_default":     (WidgetType.Switch, {}),
    }

    async def get_formfield_override(self, field_name: str):
        if field_name == "category":
            cats = await TariffCategory.all().values("id", "name")
            opts = [{"label": c["name"], "value": c["id"]} for c in cats]
            return (WidgetType.Select, {"options": opts})
        return await super().get_formfield_override(field_name)


@register(Feature)
class FeatureAdmin(TortoiseModelAdmin):
    list_display = (
        "id", "name", "name_uz", "name_ru", "name_en",
        "description", "description_uz", "description_ru", "description_en",
        "created_at"
    )
    search_fields = ("name", "name_uz", "name_ru", "name_en")

    formfield_overrides = {
        "name":           (WidgetType.Input, {}),
        "name_uz":        (WidgetType.Input, {}),
        "name_ru":        (WidgetType.Input, {}),
        "name_en":        (WidgetType.Input, {}),
        "description":    (WidgetType.TextArea, {}),
        "description_uz": (WidgetType.TextArea, {}),
        "description_ru": (WidgetType.TextArea, {}),
        "description_en": (WidgetType.TextArea, {}),
    }


@register(TariffFeature)
class TariffFeatureAdmin(TortoiseModelAdmin):
    list_display = (
        "id", "tariff", "feature", "is_included", "created_at",
    )
    list_filter = ("is_included",)
    search_fields = ("tariff", "feature")
    list_select_related = ("tariff", "feature")

    formfield_overrides = {
        "is_included": (WidgetType.Switch, {}),
    }

    async def get_formfield_override(self, field_name: str):
        if field_name == "tariff":
            tfs = await Tariff.all().values("id", "name")
            opts = [{"label": t["name"], "value": t["id"]} for t in tfs]
            return (WidgetType.Select, {"options": opts})
        if field_name == "feature":
            fts = await Feature.all().values("id", "name")
            opts = [{"label": f["name"], "value": f["id"]} for f in fts]
            return (WidgetType.Select, {"options": opts})
        return await super().get_formfield_override(field_name)


@register(Sale)
class SaleAdmin(TortoiseModelAdmin):
    list_display = (
        "id", "tariff", "percent",
        "start_date", "start_time",
        "end_date", "end_time",
        "is_active", "created_at",
    )
    list_filter = ("is_active",)
    search_fields = ("tariff",)
    list_select_related = ("tariff",)

    formfield_overrides = {
        "percent":    (WidgetType.InputNumber, {}),
        "start_date": (WidgetType.DatePicker, {}),
        "start_time": (WidgetType.TimePicker, {}),
        "end_date":   (WidgetType.DatePicker, {}),
        "end_time":   (WidgetType.TimePicker, {}),
        "is_active":  (WidgetType.Switch, {}),
    }

    async def get_formfield_override(self, field_name: str):
        if field_name == "tariff":
            sales = await Tariff.all().values("id", "name")
            opts = [{"label": s["name"], "value": s["id"]} for s in sales]
            return (WidgetType.Select, {"options": opts})
        return await super().get_formfield_override(field_name)
