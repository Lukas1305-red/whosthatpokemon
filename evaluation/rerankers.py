from collections.abc import Sequence
from typing import Protocol

from cohere import ClientV2


class Reranker(Protocol):
    def __call__(
        self, query: str, documents: Sequence[str], top_n: int
    ) -> list[tuple[int, float]]: ...


class CohereReranker:
    """Rerank vector-search candidates with Cohere's relevance model."""

    def __init__(self, client: ClientV2, model: str = "rerank-v4.0-pro"):
        self.client = client
        self.model = model

    def __call__(
        self, query: str, documents: Sequence[str], top_n: int
    ) -> list[tuple[int, float]]:
        response = self.client.rerank(
            model=self.model,
            query=query,
            documents=documents,
            top_n=top_n,
        )
        return [(result.index, result.relevance_score) for result in response.results]
