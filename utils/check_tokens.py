import logging
from fastapi import HTTPException, Request, status
from utils.get_actual_price import get_user_actual_test_price
from models.transactions import TokenTransaction, TransactionType
from tortoise.transactions import in_transaction

logger = logging.getLogger(__name__)

async def check_user_tokens(
    user,
    test_type: TransactionType,
    request: Request,
    t: dict
) -> bool:
    """
    Check if the user has enough tokens for a given test type.
    If tokens are sufficient, deduct and record a transaction.
    If insufficient, raise a 402 HTTPException with a localized message.
    """
    price = await get_user_actual_test_price(user, test_type.value.lower())
    if price is None:
        logger.error(f"Test type '{test_type}' not found in price table")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test type '{test_type}' not found"
        )

    logger.info(f"User {user.id} balance: {user.tokens}, price for '{test_type}': {price}")

    if user.tokens < price:
        logger.warning(
            f"User {user.id} has insufficient tokens for '{test_type}' "
            f"(needed {price}, has {user.tokens})"
        )
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=t.get("not_enough_tokens", "Not enough tokens")
        )

    async with in_transaction():
        user.tokens -= price
        await user.save(update_fields=["tokens"])
        await TokenTransaction.create(
            user=user,
            transaction_type=test_type,
            amount=-price,
            balance_after_transaction=user.tokens,
            description=f"Test {test_type.value} started"
        )
    logger.info(f"Deducted {price} tokens from user {user.id}; new balance is {user.tokens}")

    return True
