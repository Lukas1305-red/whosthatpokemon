from evaluation.metrics import aggregate_metrics, ndcg, reciprocal_rank


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
