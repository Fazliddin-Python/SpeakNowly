from pydantic import Field, validator
from typing import Optional
from datetime import datetime
from .base import SafeSerializer, BaseSerializer


class TokenTransactionSerializer(SafeSerializer):
    """Serializer for basic token transaction information."""
    user_id: int
    transaction_type: str
    amount: int
    balance_after_transaction: int
    description: Optional[str]


class TokenTransactionCreateSerializer(BaseSerializer):
    """Serializer for creating a token transaction."""
    user_id: int = Field(..., description="ID of the user")
    transaction_type: str = Field(..., description="Type of the transaction")
    amount: int = Field(..., description="Amount of tokens")
    description: Optional[str] = Field(None, description="Description of the transaction")

    @validator("amount")
    def validate_amount(cls, value):
        if value == 0:
            raise ValueError("Transaction amount cannot be zero")
        return value

    @validator("transaction_type")
    def validate_transaction_type(cls, value):
        valid_types = [
            "READING", "WRITING", "LISTENING", "SPEAKING",
            "DAILY_BONUS", "REFERRAL_BONUS", "CUSTOM_DEDUCTION",
            "CUSTOM_ADDITION", "REFUND"
        ]
        if value not in valid_types:
            raise ValueError(f"Invalid transaction type. Must be one of {valid_types}")
        return value


class TokenTransactionListSerializer(SafeSerializer):
    """Serializer for listing token transactions."""
    user_id: int
    transaction_type: str
    amount: int
    balance_after_transaction: int
    created_at: datetime


class TokenTransactionDetailSerializer(SafeSerializer):
    """Serializer for detailed token transaction information."""
    user: dict
    transaction_type: str
    amount: int
    balance_after_transaction: int
    description: Optional[str]
    created_at: datetime
    updated_at: datetime