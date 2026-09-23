from datetime import UTC, datetime

import pytest

from server.services.llm_budget import (
    InMemoryDailyLLMBudget,
    _seconds_until_next_utc_day,
)


def test_in_memory_budget_allows_only_its_daily_limit():
    budget = InMemoryDailyLLMBudget(limit=2)

    assert budget.reserve() is None
    assert budget.reserve() is None
    assert budget.reserve() is not None


def test_budget_reset_time_is_the_next_utc_midnight():
    now = datetime(2026, 9, 22, 23, 59, 30, tzinfo=UTC)

    assert _seconds_until_next_utc_day(now) == 30


def test_budget_rejects_an_invalid_limit():
    with pytest.raises(ValueError, match="at least 1"):
        InMemoryDailyLLMBudget(limit=0)
