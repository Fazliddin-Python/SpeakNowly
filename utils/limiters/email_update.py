import redis.asyncio as redis
from datetime import timedelta, datetime, timezone
from .base_limiter import BaseLimiter

class EmailUpdateLimiter(BaseLimiter):
    """
    Limiter for email update requests: allows only 1 update per 7 days per email.
    """
    def __init__(
        self,
        redis_client: redis.Redis,
        period: timedelta = timedelta(days=7)
    ):
        super().__init__(redis_client, prefix="email_update_last")
        self.period = period

    async def is_blocked(self, email: str) -> bool:
        """
        Returns True if the email was updated less than 7 days ago.
        """
        key = self.get_key(email)
        last_update = await self.redis.get(key)
        if last_update:
            last_dt = datetime.fromisoformat(last_update)
            if datetime.now(timezone.utc) - last_dt < self.period:
                return True
        return False

    async def register_failed_attempt(self, email: str) -> None:
        """
        Stores the date of the last email update attempt.
        """
        key = self.get_key(email)
        await self.redis.set(key, datetime.now(timezone.utc).isoformat())

    async def reset_attempts(self, email: str) -> None:
        """
        Resets the limiter (e.g., after a successful confirmation).
        """
        key = self.get_key(email)
        await self.redis.delete(key)
