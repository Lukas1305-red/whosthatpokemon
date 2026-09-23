"""Daily spend protection for paid explanation requests."""

from datetime import UTC, datetime, timedelta
from threading import Lock

from server.repositories.redis_repository import (
    RedisRepository,
    RedisStoreUnavailableError,
)


class BudgetStoreUnavailableError(Exception):
    """The shared budget store cannot safely authorize a paid request."""


class InMemoryDailyLLMBudget:
    """Local development fallback; use Redis for deployed instances."""

    def __init__(self, limit: int) -> None:
        if limit < 1:
            raise ValueError("limit must be at least 1")
        self.limit = limit
        self._day: str | None = None
        self._used = 0
        self._lock = Lock()

    def reserve(self) -> int | None:
        now = datetime.now(UTC)
        day = now.date().isoformat()
        with self._lock:
            if self._day != day:
                self._day = day
                self._used = 0
            self._used += 1
            return _seconds_until_next_utc_day(now) if self._used > self.limit else None


class RedisDailyLLMBudget:
    def __init__(self, redis: RedisRepository, limit: int) -> None:
        if limit < 1:
            raise ValueError("limit must be at least 1")
        self.redis = redis
        self.limit = limit

    def reserve(self) -> int | None:
        now = datetime.now(UTC)
        retry_after = _seconds_until_next_utc_day(now)
        key = f"pokemon-finder:explain-budget:{now.date().isoformat()}"
        try:
            used = self.redis.increment_with_expiry(key, retry_after)
        except RedisStoreUnavailableError as error:
            raise BudgetStoreUnavailableError() from error

        return retry_after if used > self.limit else None


def _seconds_until_next_utc_day(now: datetime) -> int:
    tomorrow = (now + timedelta(days=1)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    return max(1, int((tomorrow - now).total_seconds()))
