from pydantic import Field, UUID4, validator
from typing import Optional
from datetime import datetime, timezone
from .base import SafeSerializer, BaseSerializer
from models.payments import PaymentStatus


class PaymentSerializer(SafeSerializer):
    """Serializer for basic payment information."""
    uuid: UUID4
    user_id: int
    tariff_id: int
    amount: int
    start_date: datetime
    end_date: datetime
    status: PaymentStatus


class PaymentDetailSerializer(SafeSerializer):
    """Serializer for detailed payment information."""
    uuid: UUID4
    user: dict
    tariff: dict
    amount: int
    start_date: datetime
    end_date: datetime
    status: PaymentStatus

    @validator("user", "tariff")
    def validate_nested_objects(cls, value):
        if not value:
            raise ValueError("User and Tariff details must be provided")
        return value


class PaymentCreateSerializer(BaseSerializer):
    """Serializer for creating a payment."""
    user_id: int = Field(..., description="ID of the user making the payment")
    tariff_id: int = Field(..., description="ID of the tariff being purchased")
    start_date: Optional[datetime] = Field(None, description="Start date of the payment")
    end_date: Optional[datetime] = Field(None, description="End date of the payment")


class PaymentListSerializer(SafeSerializer):
    """Serializer for listing payments."""
    uuid: UUID4
    user_id: int
    tariff_id: int
    amount: int
    start_date: datetime
    end_date: datetime
    status: PaymentStatus