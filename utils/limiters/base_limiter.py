import redis.asyncio as redis
from datetime import timedelta, datetime, timezone

class AsyncLimiter:
    """
    Universal async rate limiter using Redis as backend.
    Allows to check, register and reset attempts for any identifier.
    """

    def __init__(self, redis_client: redis.Redis, prefix: str, max_attempts: int, period: timedelta):
        self.redis = redis_client
        self.prefix = prefix
        self.max_attempts = max_attempts
        self.period = period

    def get_key(self, identifier: str) -> str:
        """
        Generate a Redis key based on the prefix and identifier (e.g., email or IP).
        """
        return f"{self.prefix}:{identifier}"

    async def is_blocked(self, identifier: str) -> bool:
        """
        Returns True if too many attempts have been made for this identifier.
        """
        key = self.get_key(identifier)
        curr = await self.redis.get(key)
        if curr is not None and int(curr) >= self.max_attempts:
            return True
        return False

    async def register_attempt(self, identifier: str) -> None:
        """
        Record a new attempt for the identifier.
        """
        key = self.get_key(identifier)
        curr = await self.redis.get(key)
        if curr is None:
            await self.redis.setex(key, int(self.period.total_seconds()), 1)
        else:
            await self.redis.incr(key)
            await self.redis.expire(key, int(self.period.total_seconds()))

    async def reset(self, identifier: str) -> None:
        """
        Reset the attempt counter for the identifier.
        """
        key = self.get_key(identifier)
        await self.redis.delete(key)

class EmailUpdateLimiter:
    """
    Limiter for email update requests: allows only 1 update per 7 days per email.
    """
    def __init__(self, redis_client: redis.Redis, period: timedelta = timedelta(days=7)):
        self.redis = redis_client
        self.prefix = "email_update_last"
        self.period = period

    def get_key(self, email: str) -> str:
        return f"{self.prefix}:{email}"

    async def is_blocked(self, email: str) -> bool:
        """
        Returns True if the email was updated less than period ago.
        """
        key = self.get_key(email)
        last_update = await self.redis.get(key)
        if last_update:
            last_dt = datetime.fromisoformat(last_update)
            if datetime.now(timezone.utc) - last_dt < self.period:
                return True
        return False

    async def register_attempt(self, email: str) -> None:
        """
        Stores the date of the last email update attempt.
        """
        key = self.get_key(email)
        await self.redis.set(key, datetime.now(timezone.utc).isoformat())

    async def reset(self, email: str) -> None:
        """
        Resets the limiter (e.g., after a successful confirmation).
        """
        key = self.get_key(email)
        await self.redis.delete(key)
