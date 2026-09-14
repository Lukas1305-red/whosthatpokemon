import argparse
import json
import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", str(Path("data/.matplotlib").resolve()))

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

from dependencies import chroma_db_client, embedding_client
from evaluation.cohere_requests import CohereRequestExecutor
from evaluation.rerankers import CohereReranker
from scripts.evaluate_retrieval import (
    CachedQueryFormatter,
    CachedVectorRetriever,
    evaluate_rerank_strategy,
    evaluate_vector_strategy,
    load_cases,
)
from server.repositories.pokemon_repository import PokemonRepository
from server.services.query_formatter import identity_query_formatter

DEFAULT_CANDIDATE_POOLS = (10, 25, 50, 100)


def parse_candidate_pools(value: str, top_k: int) -> list[int]:
    try:
        pools = [int(pool.strip()) for pool in value.split(",")]
    except ValueError as error:
        raise argparse.ArgumentTypeError(
            "--candidate-pools must be comma-separated integers"
        ) from error

    if not pools or any(pool < top_k for pool in pools):
        raise argparse.ArgumentTypeError(
            "Every candidate pool must be at least --top-k"
        )
    if len(set(pools)) != len(pools):
        raise argparse.ArgumentTypeError("Candidate pools must be unique")
    return pools


def plot_tradeoffs(
    baseline: dict,
    candidate_pool_reports: list[dict],
    chart_path: Path,
) -> None:
    candidate_counts = [report["candidate_count"] for report in candidate_pool_reports]
    metrics = [report["metrics"] for report in candidate_pool_reports]

    figure, (quality_axis, latency_axis) = plt.subplots(1, 2, figsize=(13, 5))
    figure.suptitle("Rerank candidate-pool trade-offs", fontsize=14, fontweight="bold")

    quality_axis.plot(
        candidate_counts,
        [metric["recall_at_5"] for metric in metrics],
        marker="o",
        label="Rerank Recall@5",
    )
    quality_axis.plot(
        candidate_counts,
        [metric["ndcg_at_5"] for metric in metrics],
        marker="s",
        label="Rerank nDCG@5",
    )
    quality_axis.axhline(
        baseline["metrics"]["recall_at_5"],
        color="C0",
        linestyle="--",
        alpha=0.6,
        label="Raw Recall@5",
    )
    quality_axis.axhline(
        baseline["metrics"]["ndcg_at_5"],
        color="C1",
        linestyle="--",
        alpha=0.6,
        label="Raw nDCG@5",
    )
    quality_axis.set_xlabel("Candidates passed to reranker")
    quality_axis.set_ylabel("Quality score")
    quality_axis.set_xticks(candidate_counts)
    quality_axis.set_ylim(0, 1)
    quality_axis.grid(axis="y", alpha=0.25)
    quality_axis.legend(fontsize=8, loc="lower right")

    latency_axis.plot(
        candidate_counts,
        [metric["p50_latency_seconds"] for metric in metrics],
        marker="o",
        label="Rerank p50 latency",
    )
    latency_axis.plot(
        candidate_counts,
        [metric["p95_latency_seconds"] for metric in metrics],
        marker="s",
        label="Rerank p95 latency",
    )
    latency_axis.axhline(
        baseline["metrics"]["p50_latency_seconds"],
        color="C0",
        linestyle="--",
        alpha=0.6,
        label="Raw p50 latency",
    )
    latency_axis.axhline(
        baseline["metrics"]["p95_latency_seconds"],
        color="C1",
        linestyle="--",
        alpha=0.6,
        label="Raw p95 latency",
    )
    latency_axis.set_xlabel("Candidates passed to reranker")
    latency_axis.set_ylabel("Latency (seconds)")
    latency_axis.set_xticks(candidate_counts)
    latency_axis.set_ylim(bottom=0)
    latency_axis.grid(axis="y", alpha=0.25)
    latency_axis.legend(fontsize=8, loc="upper left")

    figure.tight_layout()
    chart_path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(chart_path, dpi=180, bbox_inches="tight")
    plt.close(figure)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate reranker quality and latency across candidate pools."
    )
    parser.add_argument(
        "--candidate-pools",
        default=",".join(str(pool) for pool in DEFAULT_CANDIDATE_POOLS),
        help="Comma-separated reranker candidate pools (default: 10,25,50,100)",
    )
    parser.add_argument(
        "--cases",
        type=Path,
        default=Path("tests/fixtures/rag_eval_cases.json"),
    )
    parser.add_argument("--case-limit", type=int)
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--rerank-model", default="rerank-v4.0-pro")
    parser.add_argument(
        "--cohere-requests-per-minute",
        type=float,
        default=8,
        help="Global Cohere request pace; use 0 to disable pacing (default: 8)",
    )
    parser.add_argument("--cohere-max-retries", type=int, default=5)
    parser.add_argument("--cohere-initial-backoff", type=float, default=5)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/eval_reports/candidate-pool-sweep.json"),
    )
    parser.add_argument(
        "--chart",
        type=Path,
        default=Path("data/eval_reports/candidate-pool-sweep.png"),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.top_k < 1:
        raise ValueError("--top-k must be positive")
    if args.case_limit is not None and args.case_limit < 1:
        raise ValueError("--case-limit must be positive")
    if args.cohere_max_retries < 0:
        raise ValueError("--cohere-max-retries cannot be negative")
    if args.cohere_initial_backoff <= 0:
        raise ValueError("--cohere-initial-backoff must be positive")

    candidate_pools = parse_candidate_pools(args.candidate_pools, args.top_k)
    cases = load_cases(args.cases)
    if args.case_limit:
        cases = cases[: args.case_limit]

    cohere_requests = CohereRequestExecutor(
        args.cohere_requests_per_minute,
        args.cohere_max_retries,
        args.cohere_initial_backoff,
    )
    vector_retriever = CachedVectorRetriever(
        PokemonRepository(chroma_db_client),
        max(candidate_pools),
        cohere_requests,
    )
    formatter_cache = CachedQueryFormatter()
    reranker = CohereReranker(embedding_client, model=args.rerank_model)

    print(
        f"Evaluating {len(cases)} cases across candidate pools "
        f"{candidate_pools} at {args.cohere_requests_per_minute:g} Cohere requests/minute."
    )
    baseline = evaluate_vector_strategy(
        "raw",
        identity_query_formatter,
        cases,
        args.top_k,
        vector_retriever,
        formatter_cache,
    )

    candidate_pool_reports = []
    for index, candidate_count in enumerate(candidate_pools, start=1):
        print(f"Reranking pool {candidate_count} ({index}/{len(candidate_pools)})")
        candidate_pool_reports.append(
            evaluate_rerank_strategy(
                f"rerank_{candidate_count}",
                identity_query_formatter,
                reranker,
                cases,
                args.top_k,
                candidate_count,
                vector_retriever,
                formatter_cache,
                cohere_requests,
            )
        )

    report = {
        "cases_file": str(args.cases),
        "candidate_pools": candidate_pools,
        "raw_baseline": baseline,
        "rerank_results": candidate_pool_reports,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    plot_tradeoffs(baseline, candidate_pool_reports, args.chart)

    for result in candidate_pool_reports:
        print(
            f"rerank_{result['candidate_count']}",
            json.dumps(result["metrics"], sort_keys=True),
        )
    print(f"Sweep data written to {args.output}")
    print(f"Trade-off chart written to {args.chart}")


if __name__ == "__main__":
    main()
