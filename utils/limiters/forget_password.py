from datetime import timedelta
from .base_limiter import BaseLimiter
import redis.asyncio as redis

class ForgetPasswordLimiter(BaseLimiter):
    def __init__(self, redis_client: redis.Redis):
        super().__init__(redis_client, prefix="forget_password")

    async def is_blocked(self, email: str) -> bool:
        return not await self.check_limit(email, limit=5, period=timedelta(minutes=15))

    async def register_failed_attempt(self, email: str) -> None:
        """
        Register a failed password reset attempt for rate limiting.
        """
        await self.check_limit(email, limit=5, period=timedelta(minutes=15))

    async def reset(self, email: str) -> None:
        """
        Reset the counter on successful password reset.
        """
        await self.reset_limit(email)
