from tortoise import fields
from .base import BaseModel

class TokenTransaction(BaseModel):
    TEST_READING = "READING"
    TEST_WRITING = "WRITING"
    TEST_LISTENING = "LISTENING"
    TEST_SPEAKING = "SPEAKING"
    DAILY_BONUS = "DAILY_BONUS"
    REFERRAL_BONUS = "REFERRAL_BONUS"
    CUSTOM_DEDUCTION = "CUSTOM_DEDUCTION"
    CUSTOM_ADDITION = "CUSTOM_ADDITION"
    REFUND = "REFUND"

    TRANSACTION_TYPES = (
        (TEST_READING, "Reading Test"),
        (TEST_WRITING, "Writing Test"),
        (TEST_LISTENING, "Listening Test"),
        (TEST_SPEAKING, "Speaking Test"),
        (DAILY_BONUS, "Daily Bonus"),
        (REFERRAL_BONUS, "Referral Bonus"),
        (CUSTOM_DEDUCTION, "Custom Deduction"),
        (CUSTOM_ADDITION, "Custom Addition"),
        (REFUND, "Refund"),
    )

    user = fields.ForeignKeyField("models.User", related_name="token_transactions", description="User")
    transaction_type = fields.CharField(max_length=20, choices=TRANSACTION_TYPES, description="Transaction Type")
    amount = fields.IntField(description="Amount")
    balance_after_transaction = fields.IntField(description="Balance After Transaction")
    description = fields.TextField(null=True, description="Description")

    class Meta:
        table = "token_transactions"
        verbose_name = "Token Transaction"
        verbose_name_plural = "Token Transactions"

    def __str__(self):
        return f"{self.transaction_type} - {self.amount} tokens"