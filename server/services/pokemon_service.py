import logging

from cohere.core.api_error import ApiError
from fastapi import HTTPException

from config import settings
from dependencies import embedding_client
from server.api.errors import AIProviderUnavailableError
from server.api.rate_limit import (
    enforce_cohere_embed_rate_limit,
    enforce_cohere_rerank_rate_limit,
)
from server.api.schemas.pokemon import PokemonSearchResult, Retrieval, SearchResult
from server.repositories.pokemon_repository import PokemonRepository

logger = logging.getLogger(__name__)


class PokemonService:
    def __init__(self, repo: PokemonRepository):
        self.repo = repo

    def search_pokemon(
        self,
        query: str,
        candidate_pool: int | None = None,
        top_k: int = 5,
    ) -> SearchResult:
        if candidate_pool is None:
            candidate_pool = settings.pokemon_rerank_candidates
        if candidate_pool < top_k:
            raise ValueError("candidate_pool must be at least top_k")

        try:
            enforce_cohere_embed_rate_limit()
            embedded_query = embedding_client.embed(
                texts=[query],
                model=settings.cohere_embedding_model,
                input_type="search_query",
                output_dimension=settings.cohere_embedding_dimension,
                embedding_types=["float"],
            )
        except HTTPException:
            # This is our own admission-control decision, so preserve its 429
            # status and Retry-After header for callers.
            raise
        except ApiError as error:
            logger.exception(
                "Cohere embedding request failed (status_code=%s).",
                error.status_code,
            )
            raise AIProviderUnavailableError() from error

        result = self.repo.search(
            embedded_query.embeddings.float[0], top_k=candidate_pool
        )
        candidate_ids = result["ids"][0]
        candidate_metadata = result["metadatas"][0]

        try:
            enforce_cohere_rerank_rate_limit()
            reranked = embedding_client.rerank(
                model=settings.cohere_rerank_model,
                query=query,
                documents=result["documents"][0],
                top_n=top_k,
            )
            candidate_indices = [item.index for item in reranked.results]
            retrieval = Retrieval(reranked=True)
        except HTTPException as error:
            if error.status_code != 429:
                raise
            logger.warning(
                "Cohere reranking is rate-limited; returning the raw vector ranking.",
                exc_info=True,
            )
            candidate_indices = list(range(min(top_k, len(candidate_ids))))
            retry_after = error.headers.get("Retry-After") if error.headers else None
            retrieval = Retrieval(
                reranked=False,
                rerank_unavailable_reason="rate_limited",
                retry_after_seconds=int(retry_after) if retry_after else None,
            )
        except ApiError as error:
            logger.warning(
                "Cohere reranking failed; returning the raw vector ranking.",
                exc_info=True,
            )
            # Authentication and malformed-request failures are persistent
            # server configuration problems. Do not quietly serve degraded
            # results forever; fail the request with a safe, retryable error.
            if 400 <= error.status_code < 500 and error.status_code != 429:
                raise AIProviderUnavailableError() from error
            candidate_indices = list(range(min(top_k, len(candidate_ids))))
            retrieval = Retrieval(
                reranked=False,
                rerank_unavailable_reason=(
                    "rate_limited" if error.status_code == 429 else "cohere_error"
                ),
            )

        return SearchResult(
            pokemon=[
                PokemonSearchResult(
                    id=candidate_ids[index],
                    name=candidate_metadata[index]["name"],
                    sprite_url=candidate_metadata[index]["sprite"],
                )
                for index in candidate_indices
            ],
            retrieval=retrieval,
        )

    def get_pokemon_by_id(self, pokemon_id: str) -> str | None:
        return self.repo.get_by_id(pokemon_id)
