import redis.asyncio as redis
from datetime import timedelta
from .base_limiter import BaseLimiter

class LoginLimiter(BaseLimiter):
    """Limiter for login attempts."""
    def __init__(
        self,
        redis_client: redis.Redis,
        max_attempts: int = 5,
        period: timedelta = timedelta(minutes=15)
    ):
        super().__init__(redis_client, prefix="login")
        self.max_attempts = max_attempts
        self.period = period

    async def is_blocked(self, email: str) -> bool:
        """True if too many login attempts have been made for this email."""
        allowed = await self.check_limit(email, limit=self.max_attempts, period=self.period)
        return not allowed

    async def register_failed_attempt(self, email: str) -> None:
        """Record a new failed login attempt."""
        await self.check_limit(email, limit=self.max_attempts, period=self.period)

    async def reset_attempts(self, email: str) -> None:
        """Reset counter after successful login."""
        await self.reset_limit(email)
