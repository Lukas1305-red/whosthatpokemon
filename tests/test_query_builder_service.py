import pytest

from server.api.schemas.pokemon import PokemonTrait
from server.services.query_builder_service import QueryBuilder


@pytest.mark.parametrize(
    ("trait", "expected_description"),
    [
        (
            PokemonTrait.RELIABLE,
            "dependable, steady, and consistent in its behavior",
        ),
        (
            PokemonTrait.INDEPENDENT,
            "self-sufficient and able to function with little external support",
        ),
        (
            PokemonTrait.CALM,
            "calm, patient, and emotionally steady",
        ),
        (
            PokemonTrait.CURIOUS,
            "curious, exploratory, and attentive to its surroundings",
        ),
        (
            PokemonTrait.PROTECTIVE,
            "caring, watchful, and responsive to others' safety",
        ),
        (
            PokemonTrait.ADAPTABLE,
            "adaptable, flexible, and responsive to changing conditions",
        ),
    ],
)
def test_build_query_uses_the_descriptive_text_for_each_trait(
    trait, expected_description
):
    query = QueryBuilder().build_query([trait], note=None)

    assert query == f"Characteristics: {expected_description}."


def test_build_query_keeps_trait_order_and_appends_a_note():
    query = QueryBuilder().build_query(
        [PokemonTrait.CALM, PokemonTrait.CURIOUS],
        note="Should suit a first-time trainer.",
    )

    assert query == (
        "Characteristics: calm, patient, and emotionally steady; curious, exploratory, "
        "and attentive to its surroundings.\n\n"
        "Additional preference: Should suit a first-time trainer."
    )


@pytest.mark.parametrize("note", [None, "", "   "])
def test_build_query_omits_an_absent_or_empty_note(note):
    query = QueryBuilder().build_query([PokemonTrait.PROTECTIVE], note)

    assert (
        query == "Characteristics: caring, watchful, and responsive to others' safety."
    )
