import time
from collections.abc import Callable
from typing import TypeVar

from cohere.core.api_error import ApiError

Result = TypeVar("Result")


class CohereRequestExecutor:
    """Pace Cohere requests and retry rate-limited calls with backoff."""

    def __init__(
        self,
        requests_per_minute: float,
        max_retries: int,
        initial_backoff_seconds: float,
    ):
        if requests_per_minute < 0:
            raise ValueError("requests_per_minute cannot be negative")
        self.minimum_interval = 60 / requests_per_minute if requests_per_minute else 0
        self.max_retries = max_retries
        self.initial_backoff_seconds = initial_backoff_seconds
        self.last_request_at: float | None = None

    def execute(self, request: Callable[[], Result]) -> Result:
        for attempt in range(self.max_retries + 1):
            self._wait_for_rate_limit()
            try:
                response = request()
            except ApiError as error:
                if error.status_code != 429 or attempt == self.max_retries:
                    raise
                wait_seconds = self._retry_delay(error, attempt)
                print(
                    f"Cohere rate limit reached; retrying in {wait_seconds:.1f}s "
                    f"({attempt + 1}/{self.max_retries})."
                )
                time.sleep(wait_seconds)
            else:
                return response

        raise RuntimeError("Cohere request retry loop exited unexpectedly")

    def _wait_for_rate_limit(self) -> None:
        if self.last_request_at is None or not self.minimum_interval:
            self.last_request_at = time.monotonic()
            return

        elapsed = time.monotonic() - self.last_request_at
        if elapsed < self.minimum_interval:
            time.sleep(self.minimum_interval - elapsed)
        self.last_request_at = time.monotonic()

    def _retry_delay(self, error: ApiError, attempt: int) -> float:
        headers = {key.lower(): value for key, value in (error.headers or {}).items()}
        retry_after = headers.get("retry-after")
        if retry_after:
            try:
                return float(retry_after)
            except ValueError:
                pass
        return self.initial_backoff_seconds * (2**attempt)
