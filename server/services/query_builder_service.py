import logging

from server.api.schemas.pokemon import PokemonTrait

logger = logging.getLogger(__name__)


class QueryBuilder:
    def build_query(self, traits: list[PokemonTrait], note: str | None) -> str:
        return ""
