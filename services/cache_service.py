import json
from redis.asyncio import Redis
from config import REDIS_URL
from datetime import timedelta, datetime, timezone


class CacheService:
    def __init__(self, redis_url=REDIS_URL):
        self.redis = Redis.from_url(redis_url, decode_responses=True)

    async def get(self, key: str):
        """
        Get an object from the cache by key.
        """
        data = await self.redis.get(key)
        if data:
            return json.loads(data)
        return None

    async def set(self, key: str, value, expire: int = 3600):
        """
        Save an object in the cache with a specified lifetime (seconds).
        """
        # For ORM object serialization, use .from_queryset/to list of dicts
        if hasattr(value, "__iter__") and not isinstance(value, str):
            # If this is a QuerySet or list of models, convert to list of dicts
            value = [v.dict() if hasattr(v, "dict") else v for v in value]
        elif hasattr(value, "dict"):
            value = value.dict()
        await self.redis.set(key, json.dumps(value, default=str), ex=expire)

    async def check_email_resend_limit(self, email: str, verification_type: str) -> dict:
        """
        Check if the email resend limit has been reached.
        """
        key = f"resend_block_{email}_{verification_type}".replace(" ", "").lower()
        blocked_until = await self.redis.get(key)

        if blocked_until:
            remaining = (datetime.fromisoformat(blocked_until) - datetime.now(timezone.utc)).total_seconds()
            if remaining > 0:
                return {
                    "blocked": True,
                    "remaining_time": {"seconds": int(remaining)},
                    "message": f"Please wait {int(remaining)} seconds before resending the code.",
                }

        block_duration = 60
        await self.redis.set(key, (datetime.now() + timedelta(seconds=block_duration)).isoformat(), ex=block_duration)
        return {"blocked": False}

# Cache service instance for import
cache = CacheService()