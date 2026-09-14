import pytest
from fastapi import HTTPException
from starlette.requests import Request

import server.api.rate_limit as rate_limit_module
from server.api.rate_limit import SlidingWindowRateLimiter


def test_limiter_allows_requests_until_the_limit_is_reached():
    now = 100.0
    limiter = SlidingWindowRateLimiter(2, 60, clock=lambda: now)

    assert limiter.retry_after_seconds("client") is None
    assert limiter.retry_after_seconds("client") is None
    assert limiter.retry_after_seconds("client") == 60


def test_limiter_allows_a_request_after_the_window_expires():
    clock = [100.0]
    limiter = SlidingWindowRateLimiter(1, 60, clock=lambda: clock[0])

    assert limiter.retry_after_seconds("client") is None
    clock[0] = 160.0

    assert limiter.retry_after_seconds("client") is None


def test_limiter_tracks_clients_independently():
    limiter = SlidingWindowRateLimiter(1, 60)

    assert limiter.retry_after_seconds("first-client") is None
    assert limiter.retry_after_seconds("second-client") is None


def test_search_endpoint_limit_returns_429_and_retry_after(monkeypatch):
    monkeypatch.setattr(
        rate_limit_module,
        "search_rate_limiter",
        SlidingWindowRateLimiter(1, 60),
    )
    request = Request({"type": "http", "client": ("127.0.0.1", 1234)})

    rate_limit_module.enforce_search_rate_limit(request)

    with pytest.raises(HTTPException) as error:
        rate_limit_module.enforce_search_rate_limit(request)

    assert error.value.status_code == 429
    assert error.value.headers == {"Retry-After": "60"}


def test_limiter_rejects_invalid_configuration():
    for max_requests, window_seconds in ((0, 60), (1, 0)):
        try:
            SlidingWindowRateLimiter(max_requests, window_seconds)
        except ValueError:
            pass
        else:
            raise AssertionError("Expected an invalid limiter configuration to fail")
