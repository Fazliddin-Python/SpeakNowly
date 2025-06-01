from tortoise import fields
from .base import BaseModel
from datetime import datetime


class TariffCategory(BaseModel):
    name = fields.CharField(max_length=255, description="Name")
    name_uz = fields.CharField(max_length=255, null=True, description="Name (Uzbek)")
    name_ru = fields.CharField(max_length=255, null=True, description="Name (Russian)")
    name_en = fields.CharField(max_length=255, null=True, description="Name (English)")
    sale = fields.DecimalField(max_digits=5, decimal_places=2, default=0, description="Sale %")
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
    old_price = fields.DecimalField(max_digits=10, decimal_places=2, null=True, description="Old Price")
    price = fields.DecimalField(max_digits=10, decimal_places=2, description="Current Price")
    price_in_stars = fields.IntField(default=0, description="Price in Stars")
    description = fields.TextField(description="Description")
    description_uz = fields.TextField(null=True, description="Description (Uzbek)")
    description_ru = fields.TextField(null=True, description="Description (Russian)")
    description_en = fields.TextField(null=True, description="Description (English)")
    tokens = fields.IntField(description="Tokens included")
    duration = fields.IntField(default=30, description="Duration (in days)")
    is_active = fields.BooleanField(default=True, description="Active")
    is_default = fields.BooleanField(default=False, description="Default")

    class Meta:
        table = "tariffs"
        verbose_name = "Tariff"
        verbose_name_plural = "Tariffs"

    def __str__(self):
        return f"{self.name} - ${self.price}"

    @classmethod
    async def get_default_tariff(cls):
        default = await cls.get_or_none(is_default=True, is_active=True)
        if default is None:
            raise RuntimeError("Default tariff not found in database.")
        return default


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
    percent = fields.IntField(default=0, description="Discount %")
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

    @property
    def is_current(self) -> bool:
        now = datetime.utcnow()
        start = datetime.combine(self.start_date, self.start_time)
        end = datetime.combine(self.end_date, self.end_time)
        return self.is_active and (start <= now <= end)

    async def get_discounted_price(self) -> float:
        if self.is_current:
            base_price = float(self.tariff.price)
            return base_price * (100 - self.percent) / 100
        return float(self.tariff.price)
