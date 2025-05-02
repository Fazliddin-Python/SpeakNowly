from pydantic import BaseModel
from typing import Optional

class TariffCategorySerializer(BaseModel):
    id: int
    name: str
    sale: float
    is_active: bool

    class Config:
        from_attributes = True


class TariffSerializer(BaseModel):
    id: int
    category_id: Optional[int]
    name: str
    price: int
    description: str
    tokens: int
    duration: int
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


class SaleSerializer(BaseModel):
    id: int
    tariff_id: int
    percent: int
    start_date: str
    end_date: str
    is_active: bool

    class Config:
        from_attributes = True


class PaymentSerializer(BaseModel):
    id: int
    user_id: int
    tariff_id: int
    amount: float
    payment_date: str
    status: str

    class Config:
        from_attributes = True