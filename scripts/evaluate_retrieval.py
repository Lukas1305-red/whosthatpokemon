import argparse
import json
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter

from evaluation.cohere_requests import CohereRequestExecutor
from evaluation.metrics import (
    aggregate_metrics,
    average_latency_seconds,
    latency_percentile_seconds,
    ndcg,
    reciprocal_rank,
)
from server.repositories.pokemon_repository import PokemonRepository
from server.services.query_formatter import identity_query_formatter


def load_cases(path: Path) -> list[dict]:
    with path.open() as file:
        cases = json.load(file)
    if not cases:
        raise ValueError(f"No evaluation cases found in {path}")
    return cases


@dataclass
class VectorSearchResult:
    candidates: list[dict]
    latency_seconds: float


class CachedVectorRetriever:
    """Avoid duplicate embeddings and Chroma queries across strategies."""

    def __init__(
        self,
        repo: PokemonRepository,
        candidate_count: int,
        cohere_requests: CohereRequestExecutor,
    ):
        self.repo = repo
        self.candidate_count = candidate_count
        self.cohere_requests = cohere_requests
        self.cache: dict[str, VectorSearchResult] = {}

    def retrieve(self, query: str) -> VectorSearchResult:
        if query not in self.cache:
            self.cache[query] = retrieve_candidates(
                self.repo,
                query,
                self.candidate_count,
                self.cohere_requests,
            )
        return self.cache[query]


class CachedQueryFormatter:
    """Use each potentially expensive formatter once per original query."""

    def __init__(self):
        self.cache: dict[tuple[int, str], tuple[str, float]] = {}

    def format(self, formatter: Callable[[str], str], query: str) -> tuple[str, float]:
        key = (id(formatter), query)
        if key not in self.cache:
            started_at = perf_counter()
            self.cache[key] = (formatter(query), perf_counter() - started_at)
        return self.cache[key]


def retrieve_candidates(
    repo: PokemonRepository,
    query: str,
    candidate_count: int,
    cohere_requests: CohereRequestExecutor,
) -> VectorSearchResult:
    from config import settings
    from dependencies import embedding_client

    embedding_latency_seconds = 0.0

    def embed_query():
        nonlocal embedding_latency_seconds
        started_at = perf_counter()
        response = embedding_client.embed(
            texts=[query],
            model=settings.cohere_embedding_model,
            input_type="search_query",
            output_dimension=settings.cohere_embedding_dimension,
            embedding_types=["float"],
        )
        embedding_latency_seconds += perf_counter() - started_at
        return response

    embedded_query = cohere_requests.execute(embed_query)
    chroma_started_at = perf_counter()
    response = repo.search(
        embedded_query.embeddings.float[0],
        top_k=candidate_count,
    )
    chroma_latency_seconds = perf_counter() - chroma_started_at
    return VectorSearchResult(
        candidates=[
            {"name": metadata["name"], "document": document}
            for metadata, document in zip(
                response["metadatas"][0], response["documents"][0], strict=True
            )
        ],
        latency_seconds=embedding_latency_seconds + chroma_latency_seconds,
    )


def evaluate_vector_strategy(
    name: str,
    formatter: Callable[[str], str],
    cases: list[dict],
    top_k: int,
    vector_retriever: CachedVectorRetriever,
    formatter_cache: CachedQueryFormatter,
) -> dict:
    rows = []
    for case in cases:
        formatted_query, formatting_latency_seconds = formatter_cache.format(
            formatter, case["query"]
        )
        vector_result = vector_retriever.retrieve(formatted_query)
        names = [candidate["name"] for candidate in vector_result.candidates[:top_k]]
        relevance = {key.lower(): value for key, value in case["relevance"].items()}
        rows.append(
            {
                "id": case["id"],
                "query": case["query"],
                "formatted_query": formatted_query,
                "results": names,
                "formatting_latency_seconds": formatting_latency_seconds,
                "vector_search_latency_seconds": vector_result.latency_seconds,
                "latency_seconds": formatting_latency_seconds
                + vector_result.latency_seconds,
                "hit_at_k": int(
                    any(relevance.get(name.lower(), 0) > 0 for name in names)
                ),
                "ndcg_at_k": ndcg(names, relevance, top_k),
                "reciprocal_rank": reciprocal_rank(names, relevance),
            }
        )

    metrics = aggregate_metrics(rows, top_k)
    add_latency_metrics(metrics, rows)
    return {
        "strategy": name,
        "top_k": top_k,
        "metrics": metrics,
        "cases": rows,
    }


def evaluate_rerank_strategy(
    name: str,
    formatter: Callable[[str], str],
    reranker: Callable[[str, list[str], int], list[tuple[int, float]]],
    cases: list[dict],
    top_k: int,
    vector_retriever: CachedVectorRetriever,
    formatter_cache: CachedQueryFormatter,
    cohere_requests: CohereRequestExecutor,
) -> dict:
    rows = []
    for case in cases:
        formatted_query, formatting_latency_seconds = formatter_cache.format(
            formatter, case["query"]
        )
        vector_result = vector_retriever.retrieve(formatted_query)
        candidates = vector_result.candidates
        rerank_latency_seconds = 0.0

        def rerank_candidates():
            nonlocal rerank_latency_seconds
            started_at = perf_counter()
            result = reranker(
                formatted_query,
                [candidate["document"] for candidate in candidates],
                top_k,
            )
            rerank_latency_seconds += perf_counter() - started_at
            return result

        reranked = cohere_requests.execute(rerank_candidates)
        results = [candidates[index]["name"] for index, _ in reranked]
        relevance = {key.lower(): value for key, value in case["relevance"].items()}
        candidate_names = [candidate["name"] for candidate in candidates]
        rows.append(
            {
                "id": case["id"],
                "query": case["query"],
                "formatted_query": formatted_query,
                "candidate_results": candidate_names,
                "candidate_hit_at_n": int(
                    any(
                        relevance.get(candidate_name.lower(), 0) > 0
                        for candidate_name in candidate_names
                    )
                ),
                "results": results,
                "rerank_scores": [score for _, score in reranked],
                "formatting_latency_seconds": formatting_latency_seconds,
                "vector_search_latency_seconds": vector_result.latency_seconds,
                "rerank_latency_seconds": rerank_latency_seconds,
                "latency_seconds": formatting_latency_seconds
                + vector_result.latency_seconds
                + rerank_latency_seconds,
                "hit_at_k": int(
                    any(relevance.get(result.lower(), 0) > 0 for result in results)
                ),
                "ndcg_at_k": ndcg(results, relevance, top_k),
                "reciprocal_rank": reciprocal_rank(results, relevance),
            }
        )

    metrics = aggregate_metrics(rows, top_k)
    add_latency_metrics(metrics, rows)
    return {
        "strategy": name,
        "top_k": top_k,
        "candidate_count": vector_retriever.candidate_count,
        "metrics": metrics,
        "cases": rows,
    }


def add_latency_metrics(metrics: dict, rows: list[dict]) -> None:
    metrics["average_latency_seconds"] = average_latency_seconds(rows)
    metrics["p50_latency_seconds"] = latency_percentile_seconds(rows, 0.50)
    metrics["p95_latency_seconds"] = latency_percentile_seconds(rows, 0.95)
    metrics["p99_latency_seconds"] = latency_percentile_seconds(rows, 0.99)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare Pokémon retrieval strategies."
    )
    parser.add_argument(
        "--strategies",
        default="raw",
        help="Comma-separated strategies: raw, llm, rerank, llm_rerank (default: raw)",
    )
    parser.add_argument(
        "--cases",
        type=Path,
        default=Path("tests/fixtures/rag_eval_cases.json"),
    )
    parser.add_argument("--case-limit", type=int)
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--llm-model", default="claude-haiku-4-5-20251001")
    parser.add_argument("--rerank-model", default="rerank-v4.0-pro")
    parser.add_argument(
        "--rerank-candidates",
        type=int,
        default=25,
        help="Number of vector candidates to rerank (default: 25)",
    )
    parser.add_argument(
        "--cohere-requests-per-minute",
        type=float,
        default=8,
        help="Global Cohere request pace; use 0 to disable pacing (default: 8)",
    )
    parser.add_argument("--cohere-max-retries", type=int, default=5)
    parser.add_argument("--cohere-initial-backoff", type=float, default=5)
    parser.add_argument(
        "--output", type=Path, default=Path("data/eval_reports/latest.json")
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.top_k < 1:
        raise ValueError("--top-k must be positive")
    if args.rerank_candidates < args.top_k:
        raise ValueError("--rerank-candidates must be at least --top-k")
    if args.case_limit is not None and args.case_limit < 1:
        raise ValueError("--case-limit must be positive")
    if args.cohere_max_retries < 0:
        raise ValueError("--cohere-max-retries cannot be negative")
    if args.cohere_initial_backoff <= 0:
        raise ValueError("--cohere-initial-backoff must be positive")

    cases = load_cases(args.cases)
    if args.case_limit:
        cases = cases[: args.case_limit]

    requested_strategies = {strategy.strip() for strategy in args.strategies.split(",")}
    strategies = {}
    if "raw" in requested_strategies:
        strategies["raw"] = identity_query_formatter

    llm_formatter = None
    if "llm" in requested_strategies or "llm_rerank" in requested_strategies:
        from dependencies import anthropic_client
        from evaluation.formatters import AnthropicQueryFormatter

        llm_formatter = AnthropicQueryFormatter(anthropic_client, model=args.llm_model)
    if "llm" in requested_strategies:
        strategies["llm"] = llm_formatter

    if "rerank" in requested_strategies or "llm_rerank" in requested_strategies:
        from dependencies import embedding_client
        from evaluation.rerankers import CohereReranker

        reranker = CohereReranker(embedding_client, model=args.rerank_model)
        if "rerank" in requested_strategies:
            strategies["rerank"] = (identity_query_formatter, reranker)
        if "llm_rerank" in requested_strategies:
            strategies["llm_rerank"] = (llm_formatter, reranker)

    unknown = requested_strategies - set(strategies)
    if unknown:
        raise ValueError(f"Unknown strategies: {', '.join(sorted(unknown))}")

    from dependencies import chroma_db_client

    candidate_count = (
        args.rerank_candidates
        if {"rerank", "llm_rerank"} & requested_strategies
        else args.top_k
    )
    cohere_requests = CohereRequestExecutor(
        args.cohere_requests_per_minute,
        args.cohere_max_retries,
        args.cohere_initial_backoff,
    )
    vector_retriever = CachedVectorRetriever(
        PokemonRepository(chroma_db_client),
        candidate_count,
        cohere_requests,
    )
    formatter_cache = CachedQueryFormatter()

    print(
        f"Evaluating {len(cases)} cases with Cohere pacing at "
        f"{args.cohere_requests_per_minute:g} requests/minute globally."
    )
    reports = []
    for name, strategy in strategies.items():
        if isinstance(strategy, tuple):
            formatter, reranker = strategy
            reports.append(
                evaluate_rerank_strategy(
                    name,
                    formatter,
                    reranker,
                    cases,
                    args.top_k,
                    vector_retriever,
                    formatter_cache,
                    cohere_requests,
                )
            )
        else:
            reports.append(
                evaluate_vector_strategy(
                    name,
                    strategy,
                    cases,
                    args.top_k,
                    vector_retriever,
                    formatter_cache,
                )
            )

    report = {"cases_file": str(args.cases), "strategies": reports}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")

    for result in reports:
        print(result["strategy"], json.dumps(result["metrics"], sort_keys=True))
    print(f"Detailed report written to {args.output}")


if __name__ == "__main__":
    main()
