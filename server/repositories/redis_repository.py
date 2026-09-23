"""Small, failure-aware interface for the Redis operations used by the API."""

from redis import Redis
from redis.exceptions import RedisError


class RedisStoreUnavailableError(Exception):
    """Redis could not complete an operation required by the application."""


class RedisRepository:
    def __init__(self, redis: Redis) -> None:
        self._redis = redis

    def get(self, key: str) -> str | None:
        try:
            return self._redis.get(key)
        except RedisError as error:
            raise RedisStoreUnavailableError() from error

    def set_with_ttl(self, key: str, value: str, ttl_seconds: int) -> None:
        try:
            self._redis.set(key, value, ex=ttl_seconds)
        except RedisError as error:
            raise RedisStoreUnavailableError() from error

    def increment_with_expiry(self, key: str, ttl_seconds: int) -> int:
        """Atomically increment a counter and give its first value an expiry."""
        try:
            pipeline = self._redis.pipeline(transaction=True)
            pipeline.incr(key)
            pipeline.expire(key, ttl_seconds, nx=True)
            used, _ = pipeline.execute()
            return used
        except RedisError as error:
            raise RedisStoreUnavailableError() from error
