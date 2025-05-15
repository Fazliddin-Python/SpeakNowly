from datetime import timedelta
from .base_limiter import BaseLimiter
import redis.asyncio as redis

class RegistrationLimiter(BaseLimiter):
    def __init__(self, redis_client: redis.Redis):
        super().__init__(redis_client, prefix="register")

    async def is_blocked(self, email: str) -> bool:
        """
        True if registration should be blocked (limit exceeded).
        """
        return not await self.check_limit(email, limit=5, period=timedelta(minutes=10))

    async def register_failed_attempt(self, email: str) -> None:
        """
        Increment the failed attempt count (same check logic).
        """
        await self.check_limit(email, limit=5, period=timedelta(minutes=10))

    async def register_successful_attempt(self, email: str) -> None:
        """
        Reset the counter on successful registration/verification.
        """
        await self.reset_limit(email)
