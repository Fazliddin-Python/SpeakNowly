from tortoise import fields
from .base import BaseModel

class TariffCategory(BaseModel):
    name = fields.CharField(max_length=255)
    name_uz = fields.CharField(max_length=255, null=True)
    name_ru = fields.CharField(max_length=255, null=True)
    name_en = fields.CharField(max_length=255, null=True)
    sale = fields.FloatField(default=0)
    is_active = fields.BooleanField(default=True)

    class Meta:
        table = "tariff_categories"

    def __str__(self):
        return self.name


class Tariff(BaseModel):
    category = fields.ForeignKeyField('models.TariffCategory', related_name='tariffs', null=True)
    name = fields.CharField(max_length=255)
    old_price = fields.IntField(null=True)
    price = fields.IntField()
    price_in_stars = fields.IntField(default=0)
    description = fields.TextField()
    description_uz = fields.TextField(null=True)
    description_ru = fields.TextField(null=True)
    description_en = fields.TextField(null=True)
    tokens = fields.IntField()
    duration = fields.IntField(default=30)
    is_active = fields.BooleanField(default=True)
    is_default = fields.BooleanField(default=False)

    class Meta:
        table = "tariffs"

    def __str__(self):
        return f"{self.name} - ${self.price}"


class Feature(BaseModel):
    name = fields.CharField(max_length=255, unique=True)
    description = fields.TextField(null=True)

    class Meta:
        table = "features"

    def __str__(self):
        return self.name


class TariffFeature(BaseModel):
    tariff = fields.ForeignKeyField('models.Tariff', related_name='tariff_features')
    feature = fields.ForeignKeyField('models.Feature', related_name='tariff_features')
    is_included = fields.BooleanField(default=True)

    class Meta:
        table = "tariff_features"

    def __str__(self):
        return f"{self.tariff.name} - {self.feature.name}"


class Sale(BaseModel):
    tariff = fields.ForeignKeyField('models.Tariff', related_name='sales')
    percent = fields.IntField(default=0)
    start_date = fields.DateField()
    start_time = fields.TimeField()
    end_date = fields.DateField()
    end_time = fields.TimeField()
    is_active = fields.BooleanField(default=True)

    class Meta:
        table = "sales"

    def __str__(self):
        return f"Sale {self.percent}% for {self.tariff.name}"
