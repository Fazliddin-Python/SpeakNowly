from pydantic import BaseModel, UUID4
from typing import Optional


class PaymentSerializer(BaseModel):
    id: int
    uuid: UUID4
    user_id: int
    tariff_id: int
    amount: int
    start_date: str
    end_date: str

    class Config:
        from_attributes = True


class PaymentDetailSerializer(BaseModel):
    id: int
    uuid: UUID4
    user: dict  # Nested user details
    tariff: dict  # Nested tariff details
    amount: int
    start_date: str
    end_date: str

    class Config:
        from_attributes = True


class PaymentCreateSerializer(BaseModel):
    user_id: int
    tariff_id: int
    amount: int
    start_date: Optional[str]
    end_date: Optional[str]

    class Config:
        from_attributes = True


class PaymentListSerializer(BaseModel):
    id: int
    uuid: UUID4
    user_id: int
    tariff_id: int
    amount: int
    start_date: str
    end_date: str

    class Config:
        from_attributes = True