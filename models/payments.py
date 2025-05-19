from tortoise import fields
from .base import BaseModel
from enum import Enum

class PaymentStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"

class Payment(BaseModel):
    uuid = fields.UUIDField(description="UUID")
    user = fields.ForeignKeyField("models.User", related_name="payments", description="User", on_delete=fields.CASCADE)
    tariff = fields.ForeignKeyField("models.Tariff", related_name="payments", description="Tariff", on_delete=fields.CASCADE)
    amount = fields.IntField(description="Amount")
    start_date = fields.DatetimeField(description="Start Date")
    end_date = fields.DatetimeField(description="End Date")
    status = fields.CharEnumField(PaymentStatus, default=PaymentStatus.PENDING, description="Payment status")

    class Meta:
        table = "payments"
        verbose_name = "Payment"
        verbose_name_plural = "Payments"

    def __str__(self):
        return f"Payment of {self.amount} by {self.user_id} for {self.tariff.name}"