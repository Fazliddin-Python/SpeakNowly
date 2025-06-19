from fastapi import APIRouter, HTTPException, status, Depends, Request
from uuid import uuid4
from datetime import datetime, timezone, timedelta
from tortoise.exceptions import DoesNotExist

from ..serializers.payments import PaymentCreateSerializer, PaymentSerializer
from services.payments.atmos_service import atm
from models import Payment, Tariff, TokenTransaction, TransactionType, Message
from utils.auth import get_current_user
from utils.i18n import get_translation

# Базовый URL фронтенда для уведомлений
FRONT_BASE = "https://speaknowly.com/dashboard/notification"

router = APIRouter()

@router.post(
    "/checkout/",
    response_model=PaymentSerializer,
    status_code=status.HTTP_201_CREATED
)
async def checkout(
    data: PaymentCreateSerializer,
    user=Depends(get_current_user),
    t=Depends(get_translation)
):
    """
    1) Проверяем тариф
    2) Не даём купить повторно уже активный
    3) Создаём или переиспользуем pending-платёж
    4) Запрашиваем у Atmos draft и получаем transaction_id
    5) Строим правильный payment_url на /pay/form
    """
    try:
        tariff = await Tariff.get(id=data.tariff_id)
    except DoesNotExist:
        raise HTTPException(404, t["tariff_not_found"])

    now = datetime.now(timezone.utc)
    paid = await Payment.filter(
        user_id=user.id,
        tariff_id=tariff.id,
        end_date__gte=now,
        status="paid"
    ).first()
    if paid:
        raise HTTPException(400, t["payment_exists"])

    payment = await Payment.filter(
        user_id=user.id,
        tariff_id=tariff.id,
        status="pending"
    ).first()
    if not payment:
        start = data.start_date or now
        end = data.end_date or (start + timedelta(days=tariff.duration))
        payment = await Payment.create(
            uuid=uuid4(),
            user=user,
            tariff=tariff,
            amount=tariff.price,
            start_date=start,
            end_date=end,
            status="pending"
        )

    # Call Atmos to create transaction draft
    try:
        invoice = await atm.create_invoice(
            amount=payment.amount * 100,    # convert to tiyin
            account=str(payment.uuid)
        )
    except Exception as e:
        raise HTTPException(502, t["atm_error"].format(error=str(e)))

    # Persist Atmos fields
    await payment.update_from_dict({
        "atmos_invoice_id": str(invoice["transaction_id"]),
        "atmos_status": invoice["result"]["code"],
        "atmos_response": invoice["store_transaction"]
    }).save()

    # Assemble final redirect URL to Atmos's hosted form
    # English comment: Build the frontend redirect to Atmos payment form
    payment_url = invoice["payment_url"]

    return PaymentSerializer(
        uuid=payment.uuid,
        user_id=user.id,
        tariff_id=tariff.id,
        amount=payment.amount,
        start_date=payment.start_date,
        end_date=payment.end_date,
        status=payment.status,
        atmos_invoice_id=str(invoice["transaction_id"]),
        atmos_status=invoice["result"]["code"],
        payment_url=payment_url
    )

@router.post("/callback/", status_code=200)
async def callback(req: Request, t=Depends(get_translation)):
    """
    Обработчик вебхука от Atmos:
    - проверяем код результата
    - отмечаем платёж как paid
    - начисляем токены
    - создаём уведомление и возвращаем redirect_url на фронт
    """
    payload = await req.json()
    txn = payload.get("transaction_id")
    code = payload.get("result", {}).get("code")
    if not txn or code != "OK":
        raise HTTPException(400, t["invalid_callback"])

    try:
        payment = await Payment.get(
            atmos_invoice_id=str(txn)
        ).prefetch_related("tariff", "user")
    except DoesNotExist:
        raise HTTPException(404, "Payment not found")

    if payment.status != "paid":
        payment.status = "paid"
        await payment.save()

        tokens = payment.tariff.tokens
        last = await TokenTransaction.filter(user_id=payment.user_id).order_by("-created_at").first()
        balance = last.balance_after_transaction if last else 0
        await TokenTransaction.create(
            user=payment.user,
            transaction_type=TransactionType.CUSTOM_ADDITION,
            amount=tokens,
            balance_after_transaction=balance + tokens,
            description=f"Tokens for {payment.tariff.name}"
        )

        # English comment: Create a notification message for the user
        msg = await Message.create(
            user=payment.user,
            type="site",
            title="Payment Successful",
            description=f"You have paid for {payment.tariff.name}.",
            content=f"{tokens} tokens added to your balance."
        )

        # English comment: Build the frontend notification URL
        redirect_url = f"{FRONT_BASE}/{msg.id}"
        return {"status": "ok", "redirect_url": redirect_url}

    return {"status": "ok"}
