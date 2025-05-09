from pydantic import Field, UUID4, validator
from typing import Optional
from datetime import datetime
from .base import SafeSerializer, BaseSerializer


class PaymentSerializer(SafeSerializer):
    """Serializer for basic payment information."""
    uuid: UUID4
    user_id: int
    tariff_id: int
    amount: int
    start_date: datetime
    end_date: datetime


class PaymentDetailSerializer(SafeSerializer):
    """Serializer for detailed payment information."""
    uuid: UUID4
    user: dict
    tariff: dict
    amount: int
    start_date: datetime
    end_date: datetime

    @validator("user", "tariff")
    def validate_nested_objects(cls, value):
        if not value:
            raise ValueError("User and Tariff details must be provided")
        return value


class PaymentCreateSerializer(BaseSerializer):
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


class PaymentListSerializer(SafeSerializer):
    """Serializer for listing payments."""
    uuid: UUID4
    user_id: int
    tariff_id: int
    amount: int
    start_date: datetime
    end_date: datetime