import argparse
import json
from collections.abc import Callable
from pathlib import Path

from evaluation.metrics import aggregate_metrics, ndcg, reciprocal_rank
from server.repositories.pokemon_repository import PokemonRepository
from server.services.pokemon_service import PokemonService
from server.services.query_formatter import identity_query_formatter


def load_cases(path: Path) -> list[dict]:
    with path.open() as file:
        cases = json.load(file)
    if not cases:
        raise ValueError(f"No evaluation cases found in {path}")
    return cases


def evaluate_strategy(
    name: str,
    formatter: Callable[[str], str],
    cases: list[dict],
    top_k: int,
) -> dict:
    # Imports are intentionally delayed so metric/unit tests do not need API keys.
    from dependencies import chroma_db_client

    service = PokemonService(
        PokemonRepository(chroma_db_client),
        # The strategy is applied once below. This avoids two LLM calls per
        # case and makes the query recorded in the report exactly the query
        # that was embedded.
        query_formatter=identity_query_formatter,
    )
    rows = []
    for case in cases:
        formatted_query = formatter(case["query"])
        results = service.search_pokemon(formatted_query, top_k=top_k)
        names = [result.name for result in results]
        relevance = {key.lower(): value for key, value in case["relevance"].items()}
        rows.append(
            {
                "id": case["id"],
                "query": case["query"],
                "formatted_query": formatted_query,
                "results": names[:top_k],
                "hit_at_k": int(
                    any(relevance.get(name.lower(), 0) > 0 for name in names[:top_k])
                ),
                "ndcg_at_k": ndcg(names, relevance, top_k),
                "reciprocal_rank": reciprocal_rank(names, relevance),
            }
        )

    return {
        "strategy": name,
        "top_k": top_k,
        "metrics": aggregate_metrics(rows, top_k),
        "cases": rows,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare Pokémon retrieval strategies."
    )
    parser.add_argument(
        "--strategies",
        default="raw",
        help="Comma-separated strategies: raw, llm (default: raw)",
    )
    parser.add_argument(
        "--cases",
        type=Path,
        default=Path("tests/fixtures/rag_eval_cases.json"),
    )
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--llm-model", default="claude-haiku-4-5-20251001")
    parser.add_argument(
        "--output", type=Path, default=Path("data/eval_reports/latest.json")
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.top_k < 1:
        raise ValueError("--top-k must be positive")

    cases = load_cases(args.cases)
    strategies = {}
    requested_strategies = {strategy.strip() for strategy in args.strategies.split(",")}
    if "raw" in requested_strategies:
        strategies["raw"] = lambda query: query
    if "llm" in requested_strategies:
        from dependencies import anthropic_client
        from evaluation.formatters import AnthropicQueryFormatter

        strategies["llm"] = AnthropicQueryFormatter(
            anthropic_client, model=args.llm_model
        )
    unknown = requested_strategies - set(strategies)
    if unknown:
        raise ValueError(f"Unknown strategies: {', '.join(sorted(unknown))}")

    reports = [
        evaluate_strategy(name, formatter, cases, args.top_k)
        for name, formatter in strategies.items()
    ]
    report = {"cases_file": str(args.cases), "strategies": reports}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")

    for result in reports:
        print(result["strategy"], json.dumps(result["metrics"], sort_keys=True))
    print(f"Detailed report written to {args.output}")


if __name__ == "__main__":
    main()
