from tortoise import fields
from .base import BaseModel

class TariffCategory(BaseModel):
    name = fields.CharField(max_length=255, description="Name")
    name_uz = fields.CharField(max_length=255, null=True, description="Name (Uzbek)")
    name_ru = fields.CharField(max_length=255, null=True, description="Name (Russian)")
    name_en = fields.CharField(max_length=255, null=True, description="Name (English)")
    sale = fields.FloatField(default=0, description="Sale")
    is_active = fields.BooleanField(default=True, description="Active")

    class Meta:
        table = "tariff_categories"
        verbose_name = "Tariff Category"
        verbose_name_plural = "Tariff Categories"

    def __str__(self):
        return self.name


class Tariff(BaseModel):
    category = fields.ForeignKeyField("models.TariffCategory", related_name="tariffs", null=True, description="Category")
    name = fields.CharField(max_length=255, description="Name")
    old_price = fields.IntField(null=True, description="Old Price")
    price = fields.IntField(description="Price")
    price_in_stars = fields.IntField(default=0, description="Price in Stars")
    description = fields.TextField(description="Description")
    description_uz = fields.TextField(null=True, description="Description (Uzbek)")
    description_ru = fields.TextField(null=True, description="Description (Russian)")
    description_en = fields.TextField(null=True, description="Description (English)")
    tokens = fields.IntField(description="Tokens")
    duration = fields.IntField(default=30, description="Duration")
    is_active = fields.BooleanField(default=True, description="Active")
    is_default = fields.BooleanField(default=False, description="Default")

    class Meta:
        table = "tariffs"
        verbose_name = "Tariff"
        verbose_name_plural = "Tariffs"

    def __str__(self):
        return f"{self.name} - ${self.price}"


class Feature(BaseModel):
    name = fields.CharField(max_length=255, unique=True, description="Feature Name")
    description = fields.TextField(null=True, description="Description")

    class Meta:
        table = "features"
        verbose_name = "Feature"
        verbose_name_plural = "Features"

    def __str__(self):
        return self.name


class TariffFeature(BaseModel):
    tariff = fields.ForeignKeyField("models.Tariff", related_name="features", description="Tariff")
    feature = fields.ForeignKeyField("models.Feature", related_name="tariff_features", description="Feature")
    is_included = fields.BooleanField(default=True, description="Is Included")

    class Meta:
        table = "tariff_features"
        verbose_name = "Tariff Feature"
        verbose_name_plural = "Tariff Features"

    def __str__(self):
        return f"{self.tariff.name} - {self.feature.name}"


class Sale(BaseModel):
    tariff = fields.ForeignKeyField("models.Tariff", related_name="sales", description="Tariff")
    percent = fields.IntField(default=0, description="Percent")
    start_date = fields.DateField(description="Start Date")
    start_time = fields.TimeField(description="Start Time")
    end_date = fields.DateField(description="End Date")
    end_time = fields.TimeField(description="End Time")
    is_active = fields.BooleanField(default=True, description="Active")

    class Meta:
        table = "sales"
        verbose_name = "Sale"
        verbose_name_plural = "Sales"

    def __str__(self):
        return f"Sale {self.percent}% for {self.tariff.name}"
