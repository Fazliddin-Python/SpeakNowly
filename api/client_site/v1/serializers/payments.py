from pydantic import BaseModel, Field, UUID4
from typing import Optional
from datetime import datetime
from models import PaymentStatus

class PaymentCreateSerializer(BaseModel):
    """Incoming payload for checkout."""
    tariff_id: int = Field(..., description="ID of tariff to purchase")
    start_date: Optional[datetime] = Field(None, description="Optional subscription start")
    end_date: Optional[datetime] = Field(None, description="Optional subscription end")

class PaymentSerializer(BaseModel):
    """Outgoing payment details."""
    uuid: UUID4 = Field(..., description="Internal payment UUID")
    user_id: int = Field(..., description="User ID")
    tariff_id: int = Field(..., description="Tariff ID")
    amount: int = Field(..., description="Amount in sum")
    start_date: datetime = Field(..., description="Subscription start")
    end_date: datetime = Field(..., description="Subscription end")
    status: PaymentStatus = Field(..., description="Current payment status")
    atmos_invoice_id: Optional[str] = Field(None, description="Atmos transaction ID")
    atmos_status: Optional[str] = Field(None, description="Atmos status code")
    payment_url: Optional[str] = Field(None, description="URL to redirect user for payment")
