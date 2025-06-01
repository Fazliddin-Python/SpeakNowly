from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime, timezone
from .base import SafeSerializer, BaseSerializer


class TariffCategorySerializer(SafeSerializer):
    """Serializer for tariff categories."""
    name: str
    name_uz: Optional[str]
    name_ru: Optional[str]
    name_en: Optional[str]
    sale: float
    is_active: bool


class FeatureSerializer(SafeSerializer):
    """Serializer for features."""
    name: str
    description: Optional[str]


class TariffFeatureSerializer(SafeSerializer):
    """Serializer for tariff features."""
    tariff_id: int
    feature_id: int
    is_included: bool


class TariffSerializer(SafeSerializer):
    """Serializer for basic tariff information."""
    category_id: Optional[int] = None
    name: Optional[str] = ""
    old_price: Optional[float] = 0
    price: Optional[float] = 0
    price_in_stars: Optional[int] = 0
    description: Optional[str] = ""
    description_uz: Optional[str] = ""
    description_ru: Optional[str] = ""
    description_en: Optional[str] = ""
    tokens: Optional[int] = 0
    duration: Optional[int] = 0
    is_active: Optional[bool] = False
    is_default: Optional[bool] = False

    @validator("price", "price_in_stars", "tokens", "duration")
    def validate_positive_values(cls, value):
        if value < 0:
            raise ValueError("Value must be non-negative")
        return value


class TariffDetailSerializer(SafeSerializer):
    """Serializer for detailed tariff information."""
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


class SaleSerializer(SafeSerializer):
    """Serializer for sales."""
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