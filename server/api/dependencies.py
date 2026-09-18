from fastapi import Depends

from dependencies import chroma_db_client
from server.repositories.pokemon_repository import PokemonRepository
from server.services.pokemon_service import PokemonService
from server.services.query_builder_service import QueryBuilder


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
