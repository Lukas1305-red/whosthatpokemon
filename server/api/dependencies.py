from fastapi import Depends

from config import settings
from dependencies import anthropic_client, chroma_db_client
from server.repositories.pokemon_repository import PokemonRepository
from server.services.explanation_cache import ExplanationCache
from server.services.llm_service import LLMService
from server.services.pokemon_service import PokemonService
from server.services.query_builder_service import QueryBuilder

explanation_cache = ExplanationCache(
    ttl_seconds=settings.explain_cache_ttl_seconds,
    max_entries=settings.explain_cache_max_entries,
)


def get_query_builder() -> QueryBuilder:
    return QueryBuilder()


def get_pokemon_repository() -> PokemonRepository:
    return PokemonRepository(
        chroma_client=chroma_db_client,
    )


def get_pokemon_service(
    repo: PokemonRepository = Depends(get_pokemon_repository),  # noqa: B008
) -> PokemonService:
    return PokemonService(
        repo=repo,
    )


def get_llm_service() -> LLMService:
    return LLMService(
        anthropic_client,
        explanation_cache=explanation_cache if settings.explain_cache_enabled else None,
    )
