import pytest
from pydantic import ValidationError

from server.api.schemas.pokemon import PokemonTrait, SearchRequest


def test_search_request_accepts_unique_traits_and_a_note():
    request = SearchRequest(
        traits=[PokemonTrait.RELIABLE, PokemonTrait.CURIOUS],
        note="Prefers a friendly companion.",
    )

    assert request.traits == [PokemonTrait.RELIABLE, PokemonTrait.CURIOUS]
    assert request.note == "Prefers a friendly companion."


@pytest.mark.parametrize(
    "traits",
    [
        [],
        [PokemonTrait.RELIABLE] * 5,
        [PokemonTrait.RELIABLE, PokemonTrait.RELIABLE],
    ],
)
def test_search_request_rejects_invalid_traits(traits):
    with pytest.raises(ValidationError):
        SearchRequest(traits=traits)


def test_search_request_rejects_a_note_longer_than_150_characters():
    with pytest.raises(ValidationError):
        SearchRequest(traits=[PokemonTrait.CALM], note="a" * 151)


def test_search_request_allows_an_omitted_note():
    request = SearchRequest(traits=[PokemonTrait.CALM])

    assert request.note is None
