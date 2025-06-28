from fastadmin import TortoiseModelAdmin, register, WidgetType
from models import User
from models.transactions import TokenTransaction, TransactionType


@register(TokenTransaction)
class TokenTransactionAdmin(TortoiseModelAdmin):
    list_display = (
        "id", "user", "transaction_type", "amount",
        "balance_after_transaction", "description", "created_at",
    )
    list_filter = ("transaction_type",)
    list_select_related = ("user",)
    search_fields = ()

    formfield_overrides = {
        "amount":                    (WidgetType.InputNumber, {}),
        "balance_after_transaction":(WidgetType.InputNumber, {}),
        "description":              (WidgetType.TextArea, {}),
        "transaction_type":         (WidgetType.Select, {
            "options": [
                {"label": "Reading Test", "value": TransactionType.TEST_READING.value},
                {"label": "Writing Test", "value": TransactionType.TEST_WRITING.value},
                {"label": "Listening Test", "value": TransactionType.TEST_LISTENING.value},
                {"label": "Speaking Test", "value": TransactionType.TEST_SPEAKING.value},
                {"label": "Daily Bonus", "value": TransactionType.DAILY_BONUS.value},
                {"label": "Referral Bonus", "value": TransactionType.REFERRAL_BONUS.value},
                {"label": "Custom Deduction", "value": TransactionType.CUSTOM_DEDUCTION.value},
                {"label": "Custom Addition", "value": TransactionType.CUSTOM_ADDITION.value},
                {"label": "Refund", "value": TransactionType.REFUND.value},
            ]
        }),
    }

    async def get_formfield_override(self, field_name: str):
        if field_name == "user":
            users = await User.all().values("id", "email")
            return (WidgetType.Select, {
                "options": [{"label": u["email"], "value": u["id"]} for u in users]
            })
        return await super().get_formfield_override(field_name)
