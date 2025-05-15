import aioredis
from datetime import timedelta, datetime, timezone


class CacheService:
    def __init__(self, redis_url="redis://localhost"):
        self.redis = aioredis.from_url(redis_url, decode_responses=True)

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