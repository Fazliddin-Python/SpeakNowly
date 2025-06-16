from fastapi import APIRouter, HTTPException, status, Query, Request, Depends
from typing import List
from tortoise.exceptions import DoesNotExist
from datetime import datetime, timezone, timedelta
from uuid import uuid4, UUID

from ..serializers.payments import (
    PaymentSerializer,
    PaymentDetailSerializer,
    PaymentCreateSerializer,
    PaymentListSerializer,
)
from services.payments import AtmosService
from models import Payment, Tariff, TokenTransaction, TransactionType, User
from utils.auth import get_current_user
from utils.i18n import get_translation

router = APIRouter()

@router.post("/checkout/", status_code=status.HTTP_201_CREATED, response_model=PaymentSerializer)
async def create_payment(
    payment_data: PaymentCreateSerializer,
    user: User = Depends(get_current_user),
    t: dict = Depends(get_translation)
):
    """Create payment and Atmos invoice."""
    try:
        tariff = await Tariff.get(id=payment_data.tariff_id)
    except DoesNotExist:
        raise HTTPException(status_code=404, detail=t.get("payment_not_found", "Tariff not found"))

    existing_payment = await Payment.filter(
        user_id=user.id,
        tariff_id=payment_data.tariff_id,
        end_date__gte=datetime.now(timezone.utc)
    ).first()
    if existing_payment:
        raise HTTPException(status_code=400, detail=t.get("payment_already_exists", "Payment already exists"))

    start_date = payment_data.start_date or datetime.now(timezone.utc)
    duration_days = getattr(tariff, "duration", 30)
    end_date = payment_data.end_date or (start_date + timedelta(days=duration_days))

    payment = await Payment.create(
        uuid=uuid4(),
        user=user,
        tariff=tariff,
        amount=tariff.price,
        start_date=start_date,
        end_date=end_date,
        status="pending"
    )

    order_id = str(payment.uuid)
    return_url = "https://your-frontend.com/payment/success"
    description = f"Payment for tariff {getattr(tariff, 'name', '')}"
    phone = getattr(user, "phone", "998901234567")

    try:
        invoice = await AtmosService.create_invoice(
            amount=tariff.price,
            order_id=order_id,
            return_url=return_url,
            description=description,
            phone=phone,
        )
        await payment.update_from_dict({
            "atmos_order_id": order_id,
            "atmos_invoice_id": invoice.get("invoice_id"),
            "atmos_status": invoice.get("status"),
            "atmos_response": invoice
        }).save()
    except Exception as exc:
        await payment.delete()
        raise HTTPException(status_code=502, detail=t.get("atmos_error", f"Atmos error: {exc}"))

    return PaymentSerializer(
        uuid=payment.uuid,
        user_id=payment.user_id,
        tariff_id=payment.tariff_id,
        amount=payment.amount,
        start_date=payment.start_date,
        end_date=payment.end_date,
        status=payment.status,
        atmos_invoice_id=invoice.get("invoice_id"),
        atmos_status=invoice.get("status"),
        payment_url=invoice.get("payment_url"),
    )

@router.get("/", response_model=List[PaymentListSerializer])
async def list_payments(
    user: User = Depends(get_current_user),
    t: dict = Depends(get_translation)
):
    """List all payments for current user."""
    payments = await Payment.filter(user_id=user.id).all()
    if not payments:
        raise HTTPException(status_code=404, detail=t.get("no_payments", "No payments found for the user"))
    return payments

@router.get("/{payment_id}/", response_model=PaymentDetailSerializer)
async def get_payment(
    payment_id: int,
    user: User = Depends(get_current_user),
    t: dict = Depends(get_translation)
):
    """Get payment by ID."""
    try:
        payment = await Payment.get(id=payment_id, user_id=user.id).prefetch_related("user", "tariff")
        return PaymentDetailSerializer(
            uuid=payment.uuid,
            user={
                "id": payment.user.id,
                "email": payment.user.email,
                "first_name": payment.user.first_name,
                "last_name": payment.user.last_name,
            },
            tariff={
                "id": payment.tariff.id,
                "name": payment.tariff.name,
                "price": payment.tariff.price,
            },
            amount=payment.amount,
            start_date=payment.start_date,
            end_date=payment.end_date,
            status=payment.status,
            atmos_invoice_id=payment.atmos_invoice_id,
            atmos_status=payment.atmos_status,
            payment_url=payment.atmos_response.get("payment_url") if payment.atmos_response else None,
        )
    except DoesNotExist:
        raise HTTPException(status_code=404, detail=t.get("payment_not_found", "Payment not found"))

@router.get("/status/{order_id}/")
async def get_payment_status(
    order_id: str,
    user: User = Depends(get_current_user),
    t: dict = Depends(get_translation)
):
    """Check payment status from Atmos."""
    try:
        status = await AtmosService.get_invoice_status(order_id)
        return status
    except Exception as exc:
        raise HTTPException(status_code=502, detail=t.get("atmos_error", f"Atmos error: {exc}"))

@router.delete("/{payment_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_payment(
    payment_id: int,
    user: User = Depends(get_current_user),
    t: dict = Depends(get_translation)
):
    """Delete payment by ID."""
    deleted_count = await Payment.filter(id=payment_id, user_id=user.id).delete()
    if not deleted_count:
        raise HTTPException(status_code=404, detail=t.get("payment_not_found", "Payment not found"))
    return {"message": t.get("payment_deleted", "Payment deleted successfully")}

@router.post("/atmos-callback/", status_code=200)
async def atmos_callback(request: Request):
    """Atmos webhook."""
    data = await request.json()
    order_id = data.get("order_id")
    status_atmos = data.get("status")
    if not order_id or not status_atmos:
        raise HTTPException(status_code=400, detail="Invalid callback data")
    try:
        payment = await Payment.get(uuid=UUID(order_id)).prefetch_related("user", "tariff")
    except DoesNotExist:
        raise HTTPException(status_code=404, detail="Payment not found")
    if status_atmos == "paid":
        if payment.status != "paid":
            await payment.update_from_dict({"status": "paid"}).save()
            tokens_to_add = getattr(payment.tariff, "tokens", 0)
            if tokens_to_add > 0:
                last_tx = await TokenTransaction.filter(user_id=payment.user_id).order_by("-created_at").first()
                current_balance = last_tx.balance_after_transaction if last_tx else 0
                new_balance = current_balance + tokens_to_add
                await TokenTransaction.create(
                    user=payment.user,
                    transaction_type=TransactionType.CUSTOM_ADDITION,
                    amount=tokens_to_add,
                    balance_after_transaction=new_balance,
                    description=f"Tokens for tariff {payment.tariff.name} payment"
                )
            return {"message": "Payment confirmed and tokens added"}
        else:
            return {"message": "Already processed"}
    elif status_atmos == "failed":
        await payment.update_from_dict({"status": "failed"}).save()
        return {"message": "Payment failed"}
    else:
        return {"message": "Status ignored"}