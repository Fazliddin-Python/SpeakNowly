from fastapi import APIRouter, HTTPException
from models.transactions import TokenTransaction
from api.client_site.v1.serializers.transactions import TokenTransactionSerializer

router = APIRouter()

@router.get("/", response_model=list[TokenTransactionSerializer])
async def get_transactions():
    transactions = await TokenTransaction.all()
    return transactions

@router.get("/{transaction_id}/", response_model=TokenTransactionSerializer)
async def get_transaction(transaction_id: int):
    transaction = await TokenTransaction.get_or_none(id=transaction_id)
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return transaction