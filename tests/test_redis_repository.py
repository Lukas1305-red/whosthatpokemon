from unittest.mock import Mock

from server.repositories.redis_repository import RedisRepository


def test_increment_with_expiry_uses_one_redis_transaction():
    redis = Mock()
    pipeline = redis.pipeline.return_value
    pipeline.execute.return_value = [3, True]
    repository = RedisRepository(redis)

    used = repository.increment_with_expiry("budget-key", ttl_seconds=60)

    assert used == 3
    redis.pipeline.assert_called_once_with(transaction=True)
    pipeline.incr.assert_called_once_with("budget-key")
    pipeline.expire.assert_called_once_with("budget-key", 60, nx=True)
    pipeline.execute.assert_called_once_with()


def test_set_with_ttl_delegates_to_redis():
    redis = Mock()
    repository = RedisRepository(redis)

    repository.set_with_ttl("cache-key", "cached explanation", ttl_seconds=60)

    redis.set.assert_called_once_with("cache-key", "cached explanation", ex=60)
