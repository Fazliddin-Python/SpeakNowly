from pydantic import BaseModel, validator
from typing import Optional, List


class FeatureInfo(BaseModel):
    """Feature information."""
    id: int
    name: str
    description: Optional[str] = ""


class FeatureItemInfo(BaseModel):
    """Tariff feature item."""
    id: int
    tariff: int
    feature: FeatureInfo
    is_included: bool


class TariffInfo(BaseModel):
    """Tariff information."""
    id: int
    name: str
    price: float
    old_price: Optional[float] = None
    description: str
    tokens: int
    duration: int
    redirect_url: str
    is_default: bool
    price_in_stars: int = 0
    features: List[FeatureItemInfo]

    @validator("price", "tokens", "duration", pre=True)
    def non_negative(cls, v):
        if isinstance(v, (int, float)) and v < 0:
            raise ValueError("Must be non-negative")
        return v


class PlanInfo(BaseModel):
    """Plan (category) information."""
    id: int
    name: str
    sale: float
    tariffs: List[TariffInfo]
