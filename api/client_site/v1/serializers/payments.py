from pydantic import BaseModel, Field, UUID4
from typing import Optional
from datetime import datetime
from models import PaymentStatus


class PaymentCreateSerializer(BaseModel):
    """Create payment."""
    user_id: int = Field(..., description="User ID")
    tariff_id: int = Field(..., description="Tariff ID")
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class PaymentSerializer(BaseModel):
    """Basic payment info."""
    uuid: UUID4
    user_id: int
    tariff_id: int
    amount: int
    start_date: datetime
    end_date: datetime
    status: PaymentStatus
    atmos_invoice_id: Optional[str]
    atmos_status: Optional[str]
    payment_url: Optional[str]


class PaymentDetailSerializer(BaseModel):
    """Detailed payment info."""
    uuid: UUID4
    user: dict
    tariff: dict
    amount: int
    start_date: datetime
    end_date: datetime
    status: PaymentStatus
    atmos_invoice_id: Optional[str]
    atmos_status: Optional[str]
    payment_url: Optional[str]


class PaymentListSerializer(BaseModel):
    """List payments."""
    uuid: UUID4
    user_id: int
    tariff_id: int
    amount: int
    start_date: datetime
    end_date: datetime
    status: PaymentStatus
    atmos_invoice_id: Optional[str]
    atmos_status: Optional[str]
    payment_url: Optional[str]