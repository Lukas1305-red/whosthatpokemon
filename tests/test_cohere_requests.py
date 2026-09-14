from cohere.core.api_error import ApiError

from evaluation.cohere_requests import CohereRequestExecutor


def test_retries_rate_limited_request(monkeypatch):
    sleeps = []
    monkeypatch.setattr("evaluation.cohere_requests.time.sleep", sleeps.append)
    attempts = 0

    def request():
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise ApiError(status_code=429, headers={"retry-after": "0.25"})
        return "success"

    executor = CohereRequestExecutor(
        requests_per_minute=0,
        max_retries=2,
        initial_backoff_seconds=1,
    )

    assert executor.execute(request) == "success"
    assert sleeps == [0.25]
