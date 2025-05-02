from pydantic import BaseModel
from typing import Optional

class TokenTransactionSerializer(BaseModel):
    id: int
    user_id: int
    transaction_type: str
    amount: int
    balance_after_transaction: int
    description: Optional[str]

    class Config:
        from_attributes = True