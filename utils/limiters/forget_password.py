from datetime import timedelta
from .base_limiter import BaseLimiter
import redis.asyncio as redis

class ForgetPasswordLimiter(BaseLimiter):
    def __init__(self, redis_client: redis.Redis):
        super().__init__(redis_client, prefix="forget_password")

    async def is_blocked(self, email: str) -> bool:
        """
        True if forget-password should be blocked (limit exceeded).
        """
        return not await self.check_limit(email, limit=5, period=timedelta(minutes=15))

    async def increment_attempts(self, email: str) -> None:
        """
        Increment the failed attempt count.
        """
        await self.check_limit(email, limit=5, period=timedelta(minutes=15))

    async def reset_attempts(self, email: str) -> None:
        """
        Reset the counter on successful password reset.
        """
        await self.reset_limit(email)
