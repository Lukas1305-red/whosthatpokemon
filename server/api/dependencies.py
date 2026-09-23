from fastapi import Depends
from redis import Redis

from config import settings
from dependencies import anthropic_client, chroma_db_client
from server.repositories.pokemon_repository import PokemonRepository
from server.repositories.redis_repository import RedisRepository
from server.services.explanation_cache import ExplanationCache, RedisExplanationCache
from server.services.llm_budget import InMemoryDailyLLMBudget, RedisDailyLLMBudget
from server.services.llm_service import LLMService
from server.services.pokemon_service import PokemonService
from server.services.query_builder_service import QueryBuilder

redis_repository = (
    RedisRepository(Redis.from_url(settings.redis_url, decode_responses=True))
    if settings.redis_url
    else None
)
explanation_cache = (
    RedisExplanationCache(redis_repository, settings.explain_cache_ttl_seconds)
    if redis_repository
    else ExplanationCache(
        ttl_seconds=settings.explain_cache_ttl_seconds,
        max_entries=settings.explain_cache_max_entries,
    )
)
llm_budget = (
    RedisDailyLLMBudget(
        redis_repository,
        limit=settings.explain_daily_llm_budget,
    )
    if redis_repository
    else InMemoryDailyLLMBudget(limit=settings.explain_daily_llm_budget)
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
        llm_budget=llm_budget,
    )
