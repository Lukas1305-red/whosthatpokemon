from pathlib import Path

from evaluation.run_candidate_pools import parse_candidate_pools, plot_tradeoffs


def test_parse_candidate_pools():
    assert parse_candidate_pools("10, 25,50", top_k=5) == [10, 25, 50]


def test_plot_tradeoffs_writes_png(tmp_path: Path):
    baseline = {
        "metrics": {
            "recall_at_5": 0.7,
            "ndcg_at_5": 0.5,
            "p50_latency_seconds": 0.2,
            "p95_latency_seconds": 0.8,
        }
    }
    reports = [
        {
            "candidate_count": 10,
            "metrics": {
                "recall_at_5": 0.8,
                "ndcg_at_5": 0.6,
                "p50_latency_seconds": 0.4,
                "p95_latency_seconds": 1.0,
            },
        },
        {
            "candidate_count": 25,
            "metrics": {
                "recall_at_5": 0.9,
                "ndcg_at_5": 0.7,
                "p50_latency_seconds": 0.5,
                "p95_latency_seconds": 1.2,
            },
        },
    ]
    chart_path = tmp_path / "tradeoffs.png"

    plot_tradeoffs(baseline, reports, chart_path)

    assert chart_path.exists()
    assert chart_path.stat().st_size > 0
