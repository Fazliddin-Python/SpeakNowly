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

class Tariff(BaseModel):
    category = fields.ForeignKeyField('models.TariffCategory', related_name='tariffs', null=True)
    name = fields.CharField(max_length=255)
    old_price = fields.IntField(null=True)
    price = fields.IntField()
    price_in_stars = fields.IntField(default=0)
    description = fields.TextField()
    tokens = fields.IntField()
    duration = fields.IntField(default=30)
    is_active = fields.BooleanField(default=True)
    is_default = fields.BooleanField(default=False)

    class Meta:
        table = "tariffs"

class Feature(BaseModel):
    name = fields.CharField(max_length=255)
    description = fields.TextField(null=True)

    class Meta:
        table = "features"

class TariffFeature(BaseModel):
    tariff = fields.ForeignKeyField('models.Tariff', related_name='tariff_features')
    feature = fields.ForeignKeyField('models.Feature', related_name='tariff_features')
    is_included = fields.BooleanField(default=True)

    class Meta:
        table = "tariff_features"

class Sale(BaseModel):
    tariff = fields.ForeignKeyField('models.Tariff', related_name='sales')
    percent = fields.IntField(default=0)
    start_date = fields.DateField()
    end_date = fields.DateField()
    is_active = fields.BooleanField(default=True)

    class Meta:
        table = "sales"