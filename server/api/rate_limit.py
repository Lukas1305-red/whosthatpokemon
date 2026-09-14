import math
import time
from collections import defaultdict, deque
from collections.abc import Callable
from threading import Lock

from fastapi import HTTPException, Request, status

from config import settings


class SlidingWindowRateLimiter:
    def __init__(
        self,
        max_requests: int,
        window_seconds: float,
        clock: Callable[[], float] = time.monotonic,
    ):
        if max_requests < 1:
            raise ValueError("max_requests must be at least 1")
        if window_seconds <= 0:
            raise ValueError("window_seconds must be greater than 0")

        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.clock = clock
        self.requests: dict[str, deque[float]] = defaultdict(deque)
        self.lock = Lock()

    def retry_after_seconds(self, key: str) -> int | None:
        now = self.clock()
        with self.lock:
            timestamps = self.requests[key]
            cutoff = now - self.window_seconds
            # Remove timestamps older than the configured window
            while timestamps and timestamps[0] <= cutoff:
                timestamps.popleft()

            if len(timestamps) >= self.max_requests:
                return max(1, math.ceil(self.window_seconds - (now - timestamps[0])))

            timestamps.append(now)
            return None


search_rate_limiter = SlidingWindowRateLimiter(
    max_requests=settings.search_rate_limit_requests,
    window_seconds=settings.search_rate_limit_window_seconds,
)

cohere_rerank_rate_limiter = SlidingWindowRateLimiter(
    max_requests=settings.cohere_rerank_limit_requests,
    window_seconds=settings.cohere_rerank_limit_window_seconds,
)

cohere_embed_rate_limiter = SlidingWindowRateLimiter(
    max_requests=settings.cohere_embed_limit_requests,
    window_seconds=settings.cohere_embed_limit_window_seconds,
)


def enforce_search_rate_limit(request: Request) -> None:
    client_host = request.client.host if request.client else "unknown"
    retry_after = search_rate_limiter.retry_after_seconds(client_host)
    if retry_after is not None:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many search requests. Please try again shortly.",
            headers={"Retry-After": str(retry_after)},
        )


def enforce_cohere_rerank_rate_limit() -> None:
    retry_after = cohere_rerank_rate_limiter.retry_after_seconds("rerank")
    if retry_after is not None:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many rerank requests. Please try again shortly.",
            headers={"Retry-After": str(retry_after)},
        )


def enforce_cohere_embed_rate_limit() -> None:
    retry_after = cohere_embed_rate_limiter.retry_after_seconds("embed")
    if retry_after is not None:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many embed requests. Please try again shortly.",
            headers={"Retry-After": str(retry_after)},
        )
