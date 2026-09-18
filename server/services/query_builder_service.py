import logging

from server.api.schemas.pokemon import PokemonTrait

logger = logging.getLogger(__name__)


class QueryBuilder:
    def __init__(self):
        self.trait_description_mapper: dict[PokemonTrait, str] = {
            PokemonTrait.RELIABLE: (
                "dependable, steady, and consistent in its behavior"
            ),
            PokemonTrait.INDEPENDENT: (
                "self-sufficient and able to function with little external support"
            ),
            PokemonTrait.CALM: "calm, patient, and emotionally steady",
            PokemonTrait.CURIOUS: (
                "curious, exploratory, and attentive to its surroundings"
            ),
            PokemonTrait.PROTECTIVE: (
                "caring, watchful, and responsive to others' safety"
            ),
            PokemonTrait.ADAPTABLE: (
                "adaptable, flexible, and responsive to changing conditions"
            ),
        }

    def build_query(self, traits: list[PokemonTrait], note: str | None) -> str:
        trait_descriptions = [self.__get_extensive_trait(trait) for trait in traits]
        query = f"Characteristics: {'; '.join(trait_descriptions)}."

        if note and (cleaned_note := note.strip()):
            query += f"\n\nAdditional preference: {cleaned_note}"

        logger.debug("Search query for DB: %s", query)
        return query

    def __get_extensive_trait(self, trait: PokemonTrait) -> str:
        return self.trait_description_mapper[trait]
