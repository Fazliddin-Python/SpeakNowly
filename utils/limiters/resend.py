import redis.asyncio as redis
from datetime import timedelta
from .base_limiter import BaseLimiter


class ResendLimiter(BaseLimiter):
    """
    Limiter for resending verification codes.
    Blocks further resend attempts after max_attempts within the window.
    """

    def __init__(
        self,
        redis_client: redis.Redis,
        max_attempts: int = 3,
        period: timedelta = timedelta(minutes=5)
    ):
        # Ключи будут вида "resend:register:email@example.com"
        super().__init__(redis_client, prefix="resend")

        self.max_attempts = max_attempts
        self.period = period

    def _make_key(self, email: str, verification_type: str) -> str:
        """
        Комбинируем префикс, тип верификации и email в единый ключ.
        """
        identifier = f"{verification_type}:{email}"
        return self.get_key(identifier)

    async def is_blocked(self, email: str, verification_type: str) -> bool:
        """
        True, если количество повторных отправок превысило max_attempts.
        """
        key = self._make_key(email, verification_type)
        # check_limit вернёт True если можно увеличивать (ещё не превысили)
        allowed = await self.check_limit(key, limit=self.max_attempts, period=self.period)
        return not allowed

    async def register_attempt(self, email: str, verification_type: str) -> None:
        """
        Зарегистрировать попытку повторной отправки (инкремент счётчика).
        """
        key = self._make_key(email, verification_type)
        await self.check_limit(key, limit=self.max_attempts, period=self.period)

    async def reset(self, email: str, verification_type: str) -> None:
        """
        Сбросить счётчик после успешного подтверждения кода.
        """
        key = self._make_key(email, verification_type)
        await self.reset_limit(key)
