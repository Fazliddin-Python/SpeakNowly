from pydantic import BaseModel
from typing import Optional, List


class TariffCategorySerializer(BaseModel):
    id: int
    name: str
    name_uz: Optional[str]
    name_ru: Optional[str]
    name_en: Optional[str]
    sale: float
    is_active: bool

    class Config:
        from_attributes = True


class FeatureSerializer(BaseModel):
    id: int
    name: str
    description: Optional[str]

    class Config:
        from_attributes = True


class TariffFeatureSerializer(BaseModel):
    id: int
    tariff_id: int
    feature_id: int
    is_included: bool

    class Config:
        from_attributes = True


class TariffSerializer(BaseModel):
    id: int
    category_id: Optional[int]
    name: str
    old_price: Optional[int]
    price: int
    price_in_stars: int
    description: str
    description_uz: Optional[str]
    description_ru: Optional[str]
    description_en: Optional[str]
    tokens: int
    duration: int
    is_active: bool
    is_default: bool

    class Config:
        from_attributes = True


class TariffDetailSerializer(BaseModel):
    id: int
    category: Optional[TariffCategorySerializer]
    name: str
    old_price: Optional[int]
    price: int
    price_in_stars: int
    description: str
    description_uz: Optional[str]
    description_ru: Optional[str]
    description_en: Optional[str]
    tokens: int
    duration: int
    is_active: bool
    is_default: bool
    features: List[FeatureSerializer]

    class Config:
        from_attributes = True


class SaleSerializer(BaseModel):
    id: int
    tariff_id: int
    percent: int
    start_date: str
    start_time: str
    end_date: str
    end_time: str
    is_active: bool

    class Config:
        from_attributes = True