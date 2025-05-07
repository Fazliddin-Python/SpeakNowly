from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime


class TariffCategorySerializer(BaseModel):
    """Serializer for tariff categories."""
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
    """Serializer for features."""
    id: int
    name: str
    description: Optional[str]

    class Config:
        from_attributes = True


class TariffFeatureSerializer(BaseModel):
    """Serializer for tariff features."""
    id: int
    tariff_id: int
    feature_id: int
    is_included: bool

    class Config:
        from_attributes = True


class TariffSerializer(BaseModel):
    """Serializer for basic tariff information."""
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

    @validator("price", "price_in_stars", "tokens", "duration")
    def validate_positive_values(cls, value):
        if value < 0:
            raise ValueError("Value must be non-negative")
        return value

    class Config:
        from_attributes = True


class TariffDetailSerializer(BaseModel):
    """Serializer for detailed tariff information."""
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
    """Serializer for sales."""
    id: int
    tariff_id: int
    percent: int = Field(..., ge=0, le=100, description="Discount percentage (0-100)")
    start_date: str
    start_time: str
    end_date: str
    end_time: str
    is_active: bool

    @validator("start_date", "end_date", pre=True)
    def validate_date_format(cls, value):
        try:
            datetime.strptime(value, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Date must be in the format YYYY-MM-DD")
        return value

    class Config:
        from_attributes = True