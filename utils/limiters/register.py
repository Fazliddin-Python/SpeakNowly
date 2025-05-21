import redis.asyncio as redis
from datetime import timedelta
from .base_limiter import BaseLimiter

class RegistrationLimiter(BaseLimiter):
    """Limiter for registration attempts."""
    def __init__(
        self,
        redis_client: redis.Redis,
        max_attempts: int = 5,
        period: timedelta = timedelta(minutes=10)
    ):
        super().__init__(redis_client, prefix="register")
        self.max_attempts = max_attempts
        self.period = period

    async def is_blocked(self, email: str) -> bool:
        """True if too many OTP requests have been made for this email."""
        allowed = await self.check_limit(email, limit=self.max_attempts, period=self.period)
        return not allowed

    async def register_failed_attempt(self, email: str) -> None:
        """Record a new OTP request."""
        await self.check_limit(email, limit=self.max_attempts, period=self.period)

    async def reset_attempts(self, email: str) -> None:
        """Reset counter after successful registration."""
        await self.reset_limit(email)
