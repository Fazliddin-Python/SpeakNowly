import redis.asyncio as redis
from datetime import timedelta
from .base_limiter import BaseLimiter

class ResendLimiter(BaseLimiter):
    """Limiter for resend OTP requests."""
    def __init__(
        self,
        redis_client: redis.Redis,
        max_attempts: int = 3,
        period: timedelta = timedelta(minutes=5)
    ):
        super().__init__(redis_client, prefix="resend")
        self.max_attempts = max_attempts
        self.period = period

    def _make_key(self, email: str, verification_type: str) -> str:
        """Generate a unique key for the email and verification type."""
        identifier = f"{verification_type}:{email}"
        return self.get_key(identifier)

    async def is_blocked(self, email: str, verification_type: str) -> bool:
        """True if too many resend attempts have been made for this email."""
        key = self._make_key(email, verification_type)
        allowed = await self.check_limit(key, limit=self.max_attempts, period=self.period)
        return not allowed

    async def register_attempt(self, email: str, verification_type: str) -> None:
        """Record a new resend attempt."""
        key = self._make_key(email, verification_type)
        await self.check_limit(key, limit=self.max_attempts, period=self.period)

    async def reset(self, email: str, verification_type: str) -> None:
        """Reset counter after successful resend."""
        key = self._make_key(email, verification_type)
        await self.reset_limit(key)
