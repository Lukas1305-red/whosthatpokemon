import pytest

from evaluation.metrics import (
    aggregate_metrics,
    average_latency_seconds,
    latency_percentile_seconds,
    ndcg,
    reciprocal_rank,
)


def test_reciprocal_rank_uses_first_relevant_result():
    relevance = {"pikachu": 3, "eevee": 2}
    assert reciprocal_rank(["mew", "eevee", "pikachu"], relevance) == 0.5


def test_ndcg_rewards_relevant_results_earlier():
    relevance = {"pikachu": 3, "eevee": 1}
    assert ndcg(["pikachu", "eevee"], relevance, 2) > ndcg(
        ["eevee", "pikachu"], relevance, 2
    )


def test_aggregate_metrics():
    rows = [
        {"hit_at_k": 1, "ndcg_at_k": 1.0, "reciprocal_rank": 1.0},
        {"hit_at_k": 0, "ndcg_at_k": 0.0, "reciprocal_rank": 0.0},
    ]
    assert aggregate_metrics(rows, 5) == {
        "cases": 2,
        "recall_at_5": 0.5,
        "ndcg_at_5": 0.5,
        "mrr": 0.5,
    }


def test_average_latency_seconds():
    assert average_latency_seconds(
        [{"latency_seconds": 0.2}, {"latency_seconds": 0.4}]
    ) == pytest.approx(0.3)


def test_latency_percentile_seconds_uses_linear_interpolation():
    rows = [{"latency_seconds": value} for value in [0.1, 0.2, 0.3, 0.4]]

    assert latency_percentile_seconds(rows, 0.5) == pytest.approx(0.25)
    assert latency_percentile_seconds(rows, 0.95) == pytest.approx(0.385)
