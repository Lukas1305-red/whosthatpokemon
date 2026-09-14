import math
from collections.abc import Sequence


def reciprocal_rank(results: Sequence[str], relevance: dict[str, int]) -> float:
    for rank, name in enumerate(results, start=1):
        if relevance.get(name.lower(), 0) > 0:
            return 1 / rank
    return 0.0


def ndcg(results: Sequence[str], relevance: dict[str, int], k: int) -> float:
    def dcg(values: Sequence[int]) -> float:
        return sum(
            (2**value - 1) / math.log2(rank + 1)
            for rank, value in enumerate(values, start=1)
            if value > 0
        )

    actual = [relevance.get(name.lower(), 0) for name in results[:k]]
    ideal = sorted(relevance.values(), reverse=True)[:k]
    ideal_score = dcg(ideal)
    return dcg(actual) / ideal_score if ideal_score else 0.0


def aggregate_metrics(rows: list[dict], k: int) -> dict[str, float | int]:
    if not rows:
        return {f"recall_at_{k}": 0.0, f"ndcg_at_{k}": 0.0, "mrr": 0.0, "cases": 0}

    return {
        "cases": len(rows),
        f"recall_at_{k}": sum(row["hit_at_k"] for row in rows) / len(rows),
        f"ndcg_at_{k}": sum(row["ndcg_at_k"] for row in rows) / len(rows),
        "mrr": sum(row["reciprocal_rank"] for row in rows) / len(rows),
    }


def average_latency_seconds(rows: list[dict]) -> float:
    if not rows:
        return 0.0
    return sum(row["latency_seconds"] for row in rows) / len(rows)


def latency_percentile_seconds(rows: list[dict], percentile: float) -> float:
    if not 0 <= percentile <= 1:
        raise ValueError("percentile must be between 0 and 1")
    if not rows:
        return 0.0

    values = sorted(row["latency_seconds"] for row in rows)
    position = (len(values) - 1) * percentile
    lower_index = int(position)
    upper_index = min(lower_index + 1, len(values) - 1)
    lower_value = values[lower_index]
    upper_value = values[upper_index]
    return lower_value + (upper_value - lower_value) * (position - lower_index)
