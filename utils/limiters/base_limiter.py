import redis.asyncio as redis
from datetime import timedelta


class BaseLimiter:
    def __init__(self, redis_client: redis.Redis, prefix: str):
        self.redis = redis_client
        self.prefix = prefix

    def get_key(self, identifier: str) -> str:
        """Generate a Redis key based on the prefix and identifier (e.g., email or IP)."""
        return f"{self.prefix}:{identifier}"

    async def check_limit(self, identifier: str, limit: int, period: timedelta) -> bool:
        """
        Check and increment attempt counter.
        Returns True if under limit (and increments), False if limit exceeded.
        """
        key = self.get_key(identifier)
        curr = await self.redis.get(key)
        if curr is not None and int(curr) >= limit:
            return False

        # increment (or set to 1 with expiry)
        if curr is None:
            await self.redis.setex(key, int(period.total_seconds()), 1)
        else:
            await self.redis.incr(key)
            await self.redis.expire(key, int(period.total_seconds()))
        return True

    async def reset_limit(self, identifier: str) -> None:
        """Clear the attempt counter."""
        key = self.get_key(identifier)
        await self.redis.delete(key)
