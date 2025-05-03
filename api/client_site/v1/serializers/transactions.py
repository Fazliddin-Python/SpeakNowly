from pydantic import BaseModel
from typing import Optional


class TokenTransactionSerializer(BaseModel):
    id: int
    user_id: int
    transaction_type: str
    amount: int
    balance_after_transaction: int
    description: Optional[str]
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class TokenTransactionCreateSerializer(BaseModel):
    user_id: int
    transaction_type: str
    amount: int
    description: Optional[str]

    class Config:
        from_attributes = True


class TokenTransactionListSerializer(BaseModel):
    id: int
    user_id: int
    transaction_type: str
    amount: int
    balance_after_transaction: int
    created_at: str

    class Config:
        from_attributes = True


class TokenTransactionDetailSerializer(BaseModel):
    id: int
    user: dict  # Nested user details
    transaction_type: str
    amount: int
    balance_after_transaction: int
    description: Optional[str]
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True