import redis.asyncio as redis
from datetime import timedelta
from .base_limiter import BaseLimiter

class LoginLimiter(BaseLimiter):
    """
    Limiter for login attempts by email.
    Blocks further attempts after max_attempts within the window.
    """

    def __init__(
        self,
        redis_client: redis.Redis,
        max_attempts: int = 5,
        period: timedelta = timedelta(minutes=15)
    ):
        # Prefix "login" + email will form keys like "login:user@example.com"
        super().__init__(redis_client, prefix="login")
        self.max_attempts = max_attempts
        self.period = period

    async def is_blocked(self, email: str) -> bool:
        """
        Check if login attempts for this email are blocked.
        Returns True if limit exceeded, False otherwise.
        """
        # BaseLimiter.check_limit returns True if under limit (and increments)
        # so blocked == not check_limit
        allowed = await self.check_limit(email, limit=self.max_attempts, period=self.period)
        return not allowed

    async def register_failed_attempt(self, email: str) -> None:
        """
        Record a failed login attempt (increments counter).
        """
        # We call check_limit to increment the counter
        await self.check_limit(email, limit=self.max_attempts, period=self.period)

    async def register_successful_login(self, email: str) -> None:
        """
        Reset the failed-attempt counter after a successful login.
        """
        await self.reset_limit(email)
