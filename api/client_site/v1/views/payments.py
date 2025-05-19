from fastapi import APIRouter, HTTPException, status, Query, Request, Depends
from typing import List
from tortoise.exceptions import DoesNotExist
from models.payments import Payment
from models.tariffs import Tariff
from models.users.users import User
from ..serializers.payments import (
    PaymentSerializer,
    PaymentDetailSerializer,
    PaymentCreateSerializer,
    PaymentListSerializer,
)
from uuid import uuid4, UUID
from datetime import datetime, timezone, timedelta
from services.payments.atmos_service import AtmosService
import httpx
from models.transactions import TokenTransaction, TransactionType
from utils.i18n import get_translation
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/checkout/", status_code=status.HTTP_201_CREATED)
async def create_payment(payment_data: PaymentCreateSerializer, t: dict = Depends(get_translation)):
    """
    Create a new payment for a user and tariff, and generate Atmos invoice.
    Returns payment info and payment_url for redirect.
    """
    try:
        user = await User.get(id=payment_data.user_id)
        tariff = await Tariff.get(id=payment_data.tariff_id)
    except DoesNotExist:
        logger.warning("User or tariff not found (user_id=%s, tariff_id=%s)", payment_data.user_id, payment_data.tariff_id)
        raise HTTPException(status_code=404, detail=t["payment_not_found"])

    # Check for duplicate payments (optional: only for active period)
    existing_payment = await Payment.filter(
        user_id=payment_data.user_id,
        tariff_id=payment_data.tariff_id,
        end_date__gte=datetime.now(timezone.utc)
    ).first()
    if existing_payment:
        logger.warning("Duplicate payment attempt for user %s and tariff %s", user.id, tariff.id)
        raise HTTPException(status_code=400, detail=t["payment_already_exists"])

    # Calculate start and end dates
    start_date = payment_data.start_date or datetime.now(timezone.utc)
    # tariff.duration should be in days, adjust if needed
    duration_days = getattr(tariff, "duration", 30)
    end_date = payment_data.end_date or (start_date + timedelta(days=duration_days))

    # Create payment in DB (pending)
    payment = await Payment.create(
        uuid=uuid4(),
        user=user,
        tariff=tariff,
        amount=tariff.price,
        start_date=start_date,
        end_date=end_date,
    )
    logger.info("Payment created: %s for user %s", payment.uuid, user.id)

    # Create invoice in Atmos
    order_id = str(payment.uuid)
    return_url = "https://your-frontend.com/payment/success"  # TODO: set your real frontend URL
    description = f"Payment for tariff {getattr(tariff, 'name', '')}"
    phone = getattr(user, "phone", "998901234567")  # Use real phone if available

    try:
        invoice = await AtmosService.create_invoice(
            amount=tariff.price,
            order_id=order_id,
            return_url=return_url,
            description=description,
            phone=phone,
        )
    except httpx.HTTPStatusError as exc:
        logger.error("Atmos error: %s", exc.response.text)
        await payment.delete()
        raise HTTPException(status_code=502, detail=f"Atmos error: {exc.response.text}")

    # Optionally, save invoice_id in payment (if needed)
    # await payment.update_from_dict({"invoice_id": invoice.get("invoice_id")}).save()

    return {
        "uuid": payment.uuid,
        "user_id": payment.user_id,
        "tariff_id": payment.tariff_id,
        "amount": payment.amount,
        "start_date": payment.start_date,
        "end_date": payment.end_date,
        "payment_url": invoice.get("payment_url"),
        "invoice_id": invoice.get("invoice_id"),
        "status": payment.status,
    }


@router.get("/", response_model=List[PaymentListSerializer])
async def list_payments(user_id: int = Query(..., description="ID of the user")):
    """
    List all payments for a specific user.
    """
    payments = await Payment.filter(user_id=user_id).all()
    if not payments:
        raise HTTPException(status_code=404, detail="No payments found for the user")
    return [
        {
            "uuid": p.uuid,
            "user_id": p.user_id,
            "tariff_id": p.tariff_id,
            "amount": p.amount,
            "start_date": p.start_date,
            "end_date": p.end_date,
            "status": p.status,
        }
        for p in payments
    ]


@router.get("/{payment_id}/", response_model=PaymentDetailSerializer)
async def get_payment(payment_id: int):
    """
    Retrieve a specific payment by ID.
    """
    try:
        payment = await Payment.get(id=payment_id).prefetch_related("user", "tariff")
        return {
            "uuid": payment.uuid,
            "user": {
                "id": payment.user.id,
                "email": payment.user.email,
                "first_name": payment.user.first_name,
                "last_name": payment.user.last_name,
            },
            "tariff": {
                "id": payment.tariff.id,
                "name": payment.tariff.name,
                "price": payment.tariff.price,
            },
            "amount": payment.amount,
            "start_date": payment.start_date,
            "end_date": payment.end_date,
            "status": payment.status,  # <-- required!
        }
    except DoesNotExist:
        raise HTTPException(status_code=404, detail="Payment not found")


@router.get("/status/{order_id}/")
async def get_payment_status(order_id: str):
    """
    Check payment status from Atmos.
    """
    try:
        status = await AtmosService.get_invoice_status(order_id)
        return status
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=502, detail=f"Atmos error: {exc.response.text}")


@router.delete("/{payment_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_payment(payment_id: int):
    """
    Delete a specific payment by ID.
    """
    deleted_count = await Payment.filter(id=payment_id).delete()
    if not deleted_count:
        raise HTTPException(status_code=404, detail="Payment not found")
    return {"message": "Payment deleted successfully"}


@router.post("/atmos-callback/", status_code=200)
async def atmos_callback(request: Request):
    """
    Endpoint for Atmos payment webhook.
    """
    data = await request.json()
    order_id = data.get("order_id")
    status_atmos = data.get("status")  # 'paid', 'failed', etc.

    if not order_id or not status_atmos:
        raise HTTPException(status_code=400, detail="Invalid callback data")

    try:
        payment = await Payment.get(uuid=UUID(order_id)).prefetch_related("user", "tariff")
    except DoesNotExist:
        raise HTTPException(status_code=404, detail="Payment not found")

    if status_atmos == "paid":
        if payment.status != "paid":
            await payment.update_from_dict({"status": "paid"}).save()
            logger.info("Payment %s marked as paid", payment.uuid)

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
                logger.info("Tokens %d added to user %s", tokens_to_add, payment.user_id)
            return {"message": "Payment confirmed and tokens added"}
        else:
            logger.info("Payment %s already processed", payment.uuid)
            return {"message": "Already processed"}

    elif status_atmos == "failed":
        await payment.update_from_dict({"status": "failed"}).save()
        logger.info("Payment %s marked as failed", payment.uuid)
        return {"message": "Payment failed"}
    else:
        logger.info("Payment %s callback ignored with status %s", payment.uuid, status_atmos)
        return {"message": "Status ignored"}