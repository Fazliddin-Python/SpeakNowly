from fastapi import APIRouter, HTTPException, status, Depends, Request
from uuid import uuid4
from datetime import datetime, timezone, timedelta
from tortoise.exceptions import DoesNotExist

from ..serializers.payments import (
    PaymentSerializer,
    PaymentCreateSerializer,
)
from services.payments.atmos_service import atm
from models import Payment, Tariff, TokenTransaction, TransactionType
from utils.auth import get_current_user
from utils.i18n import get_translation

router = APIRouter()

@router.post("/checkout/", response_model=PaymentSerializer, status_code=status.HTTP_201_CREATED)
async def create_payment(
    data: PaymentCreateSerializer,
    user=Depends(get_current_user),
    t=Depends(get_translation)
):
    try:
        tariff = await Tariff.get(id=data.tariff_id)
    except DoesNotExist:
        raise HTTPException(404, t.get("tariff_not_found", "Tariff not found"))

    now = datetime.now(timezone.utc)

    # 👉 Проверка на уже существующий активный платеж (оплаченный)
    active = await Payment.filter(user_id=user.id, tariff_id=tariff.id, end_date__gte=now, status="paid").first()
    if active:
        raise HTTPException(400, t.get("payment_exists", "Active payment exists"))

    # 👉 Проверка на незавершённый "pending" платеж
    existing = await Payment.filter(user_id=user.id, tariff_id=tariff.id, status="pending").first()

    if existing:
        payment = existing
    else:
        start = data.start_date or now
        end = data.end_date or (start + timedelta(days=tariff.duration))
        payment = await Payment.create(
            uuid=uuid4(), user=user, tariff=tariff,
            amount=tariff.price, start_date=start, end_date=end, status="pending"
        )

    order_id = str(payment.uuid)

    try:
        resp = await atm.create_payment(amount=tariff.price * 100, account=order_id)
    except Exception as e:
        raise HTTPException(502, t.get("atm_error", str(e)))

    await payment.update_from_dict({
        "atmos_order_id": order_id,
        "atmos_invoice_id": str(resp.transaction_id),
        "atmos_status": resp.result.get("code"),
        "atmos_response": resp.store_transaction
    }).save()

    return PaymentSerializer(
        uuid=payment.uuid,
        user_id=user.id,
        tariff_id=tariff.id,
        amount=payment.amount,
        start_date=payment.start_date,
        end_date=payment.end_date,
        status=payment.status,
        atmos_invoice_id=str(resp.transaction_id),
        atmos_status=resp.result.get("code"),
        payment_url=resp.store_transaction.get("ofd_url") or ""
    )

@router.post("/callback/", status_code=200)
async def atmos_callback(
    req: Request,
    t=Depends(get_translation)
):
    payload = await req.json()
    txn = payload.get("transaction_id")
    status_at = payload.get("result", {}).get("code")
    if not txn or not status_at:
        raise HTTPException(400, t.get("invalid_callback", "Invalid callback"))
    try:
        payment = await Payment.get(atmos_invoice_id=str(txn)).prefetch_related("tariff", "user")
    except DoesNotExist:
        raise HTTPException(404, "Payment not found")

    payment.atmos_status = status_at
    if status_at == "OK" and payment.status != "paid":
        payment.status = "paid"
        await payment.save()
        tokens = payment.tariff.tokens
        last = await TokenTransaction.filter(user_id=payment.user_id).order_by("-created_at").first()
        bal = last.balance_after_transaction if last else 0
        await TokenTransaction.create(
            user=payment.user,
            transaction_type=TransactionType.CUSTOM_ADDITION,
            amount=tokens,
            balance_after_transaction=bal + tokens,
            description=f"Tokens for tariff {payment.tariff.name}"
        )
    else:
        payment.status = "failed"
        await payment.save()

    return {"status": "ok"}
