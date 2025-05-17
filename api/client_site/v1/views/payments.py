from fastapi import APIRouter, HTTPException, Depends, status, Query
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
from uuid import uuid4
from datetime import datetime, timezone, timedelta

router = APIRouter()


@router.post("/checkout/", response_model=PaymentSerializer, status_code=status.HTTP_201_CREATED)
async def create_payment(payment_data: PaymentCreateSerializer):
    """
    Create a new payment for a user and tariff.
    """
    try:
        user = await User.get(id=payment_data.user_id)
        tariff = await Tariff.get(id=payment_data.tariff_id)
    except DoesNotExist:
        raise HTTPException(status_code=404, detail="User or Tariff not found")

    # Check for duplicate payments
    existing_payment = await Payment.filter(user_id=payment_data.user_id, tariff_id=payment_data.tariff_id).first()
    if existing_payment:
        raise HTTPException(status_code=400, detail="Payment for this tariff already exists")

    # Calculate start and end dates
    start_date = payment_data.start_date or datetime.now(timezone.utc)
    end_date = payment_data.end_date or (start_date + timedelta(days=tariff.duration))

    # Create payment
    payment = await Payment.create(
        uuid=uuid4(),
        user=user,
        tariff=tariff,
        amount=tariff.price,
        start_date=start_date,
        end_date=end_date,
    )

    return payment


@router.post("/info/", response_model=PaymentDetailSerializer)
async def get_payment_info(payment_data: PaymentCreateSerializer):
    """
    Retrieve payment information for a user and tariff.
    """
    try:
        user = await User.get(id=payment_data.user_id)
        tariff = await Tariff.get(id=payment_data.tariff_id)
    except DoesNotExist:
        raise HTTPException(status_code=404, detail="User or Tariff not found")

    return {
        "id": None,
        "uuid": None,
        "user": {
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
        },
        "tariff": {
            "id": tariff.id,
            "name": tariff.name,
            "price": tariff.price,
        },
        "amount": tariff.price,
        "start_date": None,
        "end_date": None,
    }


@router.get("/", response_model=List[PaymentListSerializer])
async def list_payments(user_id: int = Query(..., description="ID of the user")):
    """
    List all payments for a specific user.
    """
    payments = await Payment.filter(user_id=user_id).all()
    if not payments:
        raise HTTPException(status_code=404, detail="No payments found for the user")
    return payments


@router.get("/{payment_id}/", response_model=PaymentDetailSerializer)
async def get_payment(payment_id: int):
    """
    Retrieve a specific payment by ID.
    """
    try:
        payment = await Payment.get(id=payment_id).prefetch_related("user", "tariff")
        return {
            "id": payment.id,
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
        }
    except DoesNotExist:
        raise HTTPException(status_code=404, detail="Payment not found")


@router.delete("/{payment_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_payment(payment_id: int):
    """
    Delete a specific payment by ID.
    """
    deleted_count = await Payment.filter(id=payment_id).delete()
    if not deleted_count:
        raise HTTPException(status_code=404, detail="Payment not found")
    return {"message": "Payment deleted successfully"}