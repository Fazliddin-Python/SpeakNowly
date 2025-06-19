from pydantic import BaseModel, Field, UUID4
from typing import Optional
from datetime import datetime
from models import PaymentStatus

class PaymentCreateSerializer(BaseModel):
    """Serializer for creating a payment request."""
    tariff_id: int = Field(..., description="Tariff ID")
    return_url: str = Field(..., description="Frontend return URL after payment")
    start_date: Optional[datetime] = Field(None, description="Optional subscription start date")
    end_date: Optional[datetime] = Field(None, description="Optional subscription end date")

class PaymentSerializer(BaseModel):
    """Serializer for returning payment details."""
    uuid: UUID4 = Field(..., description="Internal payment UUID")
    user_id: int = Field(..., description="User ID who made the payment")
    tariff_id: int = Field(..., description="ID of the purchased tariff")
    amount: int = Field(..., description="Amount in sum")
    start_date: datetime = Field(..., description="Subscription start")
    end_date: datetime = Field(..., description="Subscription end")
    status: PaymentStatus = Field(..., description="Current payment status")
    atmos_invoice_id: Optional[str] = Field(None, description="Atmos transaction ID")
    atmos_status: Optional[str] = Field(None, description="Status code returned by Atmos")
    payment_url: Optional[str] = Field(None, description="Redirect URL to complete the payment")
