from pydantic import BaseModel, UUID4, Field, validator
from typing import Optional
from datetime import datetime


class PaymentSerializer(BaseModel):
    """Serializer for basic payment information."""
    id: int
    uuid: UUID4
    user_id: int
    tariff_id: int
    amount: int
    start_date: datetime
    end_date: datetime

    class Config:
        from_attributes = True


class PaymentDetailSerializer(BaseModel):
    """Serializer for detailed payment information."""
    id: int
    uuid: UUID4
    user: dict  # Nested user details
    tariff: dict  # Nested tariff details
    amount: int = Field(..., ge=0, description="Payment amount (must be non-negative)")
    start_date: datetime
    end_date: datetime

    @validator("user", "tariff")
    def validate_nested_objects(cls, value):
        if not value:
            raise ValueError("User and Tariff details must be provided")
        return value

    class Config:
        from_attributes = True


class PaymentCreateSerializer(BaseModel):
    """Serializer for creating a payment."""
    user_id: int = Field(..., description="ID of the user making the payment")
    tariff_id: int = Field(..., description="ID of the tariff being purchased")
    amount: int = Field(..., ge=0, description="Payment amount (must be non-negative)")
    start_date: Optional[datetime] = Field(None, description="Start date of the payment")
    end_date: Optional[datetime] = Field(None, description="End date of the payment")

    @validator("end_date")
    def validate_dates(cls, end_date, values):
        start_date = values.get("start_date")
        if start_date and end_date and start_date >= end_date:
            raise ValueError("End date must be greater than start date")
        return end_date

    class Config:
        from_attributes = True


class PaymentListSerializer(BaseModel):
    """Serializer for listing payments."""
    id: int
    uuid: UUID4
    user_id: int
    tariff_id: int
    amount: int
    start_date: datetime
    end_date: datetime

    class Config:
        from_attributes = True