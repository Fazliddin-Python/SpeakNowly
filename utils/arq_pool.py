from functools import lru_cache
from arq import create_pool
from arq.connections import RedisSettings

@lru_cache()
def get_redis_settings() -> RedisSettings:
    """
    Returns cached Redis settings for ARQ.
    """
    return RedisSettings(host="localhost", port=6379)

async def get_arq_redis():
    """
    FastAPI dependency: returns a ready-to-use Redis pool for ARQ.
    """
    settings = get_redis_settings()
    return await create_pool(settings)
