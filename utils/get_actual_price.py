from tortoise.exceptions import DoesNotExist
from models import User
from models.tests import TestType

async def get_user_actual_test_price(user: User, test_type: str) -> float | None:
    """
    Get the actual price for a test for the given user and test type.
    Returns trial price if user has default tariff, otherwise returns regular price.
    Returns None if test type does not exist.
    """
    try:
        test = await TestType.get(type=test_type)
    except DoesNotExist:
        return None

    await user.fetch_related("tariff")

    if not user.tariff or user.tariff.is_default:
        return test.trial_price
    return test.price
