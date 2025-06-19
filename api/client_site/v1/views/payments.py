from fastapi import APIRouter, HTTPException, status, Depends, Request
from uuid import uuid4
from datetime import datetime, timezone, timedelta
from tortoise.exceptions import DoesNotExist
import hashlib

from ..serializers.payments import PaymentSerializer, PaymentCreateSerializer
from services.payments.atmos_service import atm
from models import Payment, Tariff, TokenTransaction, TransactionType
from utils.auth import get_current_user
from utils.i18n import get_translation

router = APIRouter()

@router.post("/checkout/", response_model=PaymentSerializer, status_code=status.HTTP_201_CREATED)
async def checkout(data: PaymentCreateSerializer, user=Depends(get_current_user), t=Depends(get_translation)):
    """Create or reuse a pending payment, then generate an Atmos invoice URL"""
    try:
        tariff = await Tariff.get(id=data.tariff_id)
    except DoesNotExist:
        raise HTTPException(404, t.get("tariff_not_found", "Tariff not found"))

    now = datetime.now(timezone.utc)
    active = await Payment.filter(
        user_id=user.id, tariff_id=tariff.id, end_date__gte=now, status="paid"
    ).first()
    if active:
        raise HTTPException(400, t.get("payment_exists", "Active payment exists"))

    payment = await Payment.filter(user_id=user.id, tariff_id=tariff.id, status="pending").first()
    if not payment:
        start_date = data.start_date or now
        end_date = data.end_date or (start_date + timedelta(days=tariff.duration))
        payment = await Payment.create(
            uuid=uuid4(), user=user, tariff=tariff,
            amount=tariff.price, start_date=start_date, end_date=end_date, status="pending"
        )

    try:
        invoice = await atm.create_invoice(
            amount=payment.amount,
            account=str(payment.id),
            redirect_link=f"https://speaknowly.com/complete?payment={payment.id}"
        )
    except Exception as e:
        raise HTTPException(502, t.get("atm_error", str(e)))

    await payment.update_from_dict({
        "atmos_invoice_id": str(invoice.payment_id),
        "atmos_status": "created",
        "atmos_response": {"url": invoice.url}
    }).save()

    return PaymentSerializer(
        uuid=payment.uuid,
        user_id=user.id,
        tariff_id=tariff.id,
        amount=payment.amount,
        start_date=payment.start_date,
        end_date=payment.end_date,
        status=payment.status,
        atmos_invoice_id=str(invoice.payment_id),
        atmos_status="created",
        payment_url=invoice.url
    )

@router.post("/callback/", status_code=200)
async def callback(req: Request, t=Depends(get_translation)):
    """Process Atmos callback: verify signature and update payment status"""
    payload = await req.json()
    invoice_id = payload.get("invoice")
    if not invoice_id:
        raise HTTPException(400, t.get("invalid_callback", "Invalid callback"))

    # Verify callback signature to prevent tampering
    signature = payload.get("sign")
    combo = (
        f"{payload.get('store_id')}{payload.get('transaction_id')}"
        f"{invoice_id}{payload.get('amount')}{atm.secret}"
    )
    if hashlib.sha256(combo.encode()).hexdigest() != signature:
        raise HTTPException(400, "Invalid signature")

    try:
        payment = await Payment.get(atmos_invoice_id=str(invoice_id)).prefetch_related("tariff", "user")
    except DoesNotExist:
        raise HTTPException(404, "Payment not found")

    if payment.status != "paid":
        payment.status = "paid"
        await payment.save()
        tokens = payment.tariff.tokens
        last_tx = await TokenTransaction.filter(user_id=payment.user_id).order_by("-created_at").first()
        balance = last_tx.balance_after_transaction if last_tx else 0
        await TokenTransaction.create(
            user=payment.user,
            transaction_type=TransactionType.CUSTOM_ADDITION,
            amount=tokens,
            balance_after_transaction=balance + tokens,
            description=f"Tokens for tariff {payment.tariff.name}"
        )

    return {"status": "ok"}
