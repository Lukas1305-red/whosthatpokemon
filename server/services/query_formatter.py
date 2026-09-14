from collections.abc import Callable
from typing import Protocol


class QueryFormatter(Protocol):
    def __call__(self, query: str) -> str: ...


def identity_query_formatter(query: str) -> str:
    """Preserve the current behavior: embed the recruiter's query unchanged."""
    return query


def make_query_formatter(formatter: Callable[[str], str] | None) -> QueryFormatter:
    return formatter or identity_query_formatter
