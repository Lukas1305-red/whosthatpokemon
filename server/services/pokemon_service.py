import logging

from cohere.core.api_error import ApiError
from fastapi import HTTPException

from config import settings
from dependencies import embedding_client
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

        enforce_cohere_embed_rate_limit()
        embedded_query = embedding_client.embed(
            texts=[query],
            model=settings.cohere_embedding_model,
            input_type="search_query",
            output_dimension=settings.cohere_embedding_dimension,
            embedding_types=["float"],
        )
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
            logger.warning(
                "Cohere reranking is rate-limited; returning the raw vector ranking.",
                exc_info=True,
            )
            candidate_indices = list(range(top_k))
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
            candidate_indices = list(range(top_k))
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
