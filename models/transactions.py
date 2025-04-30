from tortoise import fields
from .base import BaseModel
from gettext import gettext as _

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
        (TEST_READING, _("Reading Test")),
        (TEST_WRITING, _("Writing Test")),
        (TEST_LISTENING, _("Listening Test")),
        (TEST_SPEAKING, _("Speaking Test")),
        (DAILY_BONUS, _("Daily Bonus")),
        (REFERRAL_BONUS, _("Referral Bonus")),
        (CUSTOM_DEDUCTION, _("Custom Deduction")),
        (CUSTOM_ADDITION, _("Custom Addition")),
        (REFUND, _("Refund")),
    )

    user = fields.ForeignKeyField("models.User", related_name="token_transactions", description=_("User"))
    transaction_type = fields.CharField(max_length=20, choices=TRANSACTION_TYPES, description=_("Transaction Type"))
    amount = fields.IntField(description=_("Amount"))
    balance_after_transaction = fields.IntField(description=_("Balance After Transaction"))
    description = fields.TextField(null=True, description=_("Description"))

    class Meta:
        table = "token_transactions"