from celery_app import celery_app
from models.users import User
from models.tariffs import Tariff
from models.payments import Payment
from models.notifications import Message
from models.transactions import TokenTransaction
from datetime import datetime, timezone

@celery_app.task(name="tasks.tariffs.check_expired_tariffs")
async def check_expired_tariffs():
    """Check and downgrade expired user tariffs."""
    now = datetime.now(timezone.utc)
    default_tariff = await Tariff.filter(is_default=True).first()
    users = await User.all().prefetch_related("tariff")
    for user in users:
        current_payment = await Payment.filter(user_id=user.id).order_by("-end_date").first()
        if not current_payment:
            continue
        if current_payment.end_date < now and user.tariff_id and not (await Tariff.get(id=user.tariff_id)).is_default:
            expired_tariff = await Tariff.get(id=user.tariff_id)
            user.tariff_id = default_tariff.id
            await user.save(update_fields=["tariff_id"])
            await Message.create(
                user_id=user.id,
                title="📅 Tariff Expired",
                type="site",
                description="Your subscription has expired.",
                content=(
                    f"Your subscription to **{expired_tariff.name}** expired on "
                    f"{current_payment.end_date.strftime('%Y-%m-%d %H:%M')}.\n\n"
                    f"You have been switched to the default plan: **{default_tariff.name}**."
                )
            )

@celery_app.task(name="tasks.tariffs.give_daily_tariff_bonus")
async def give_daily_tariff_bonus():
    """Give daily bonus tokens to users with active tariffs."""
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    users = await User.filter(tariff_id__not=None).prefetch_related("tariff")
    for user in users:
        tariff = await Tariff.get_or_none(id=user.tariff_id)
        if not tariff or tariff.is_default:
            continue
        exists = await TokenTransaction.filter(
            user_id=user.id,
            transaction_type=TokenTransaction.DAILY_BONUS,
            created_at__gte=today_start
        ).exists()
        if exists:
            continue
        user.tokens = tariff.tokens
        await user.save(update_fields=["tokens"])
        await TokenTransaction.create(
            user_id=user.id,
            transaction_type=TokenTransaction.DAILY_BONUS,
            amount=tariff.tokens,
            balance_after_transaction=user.tokens,
            description=f"Daily bonus for {tariff.name} on {now:%Y-%m-%d}"
        )
        await Message.create(
            user_id=user.id,
            title="🎁 Daily Bonus Received",
            type="site",
            description="Your daily token bonus has been credited.",
            content=(
                f"You received **{tariff.tokens} TOKENS** for the tariff **{tariff.name}** "
                f"on {now.strftime('%Y-%m-%d')}. Previous unused tokens have been reset."
            )
        )