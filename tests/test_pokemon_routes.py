from fastapi.testclient import TestClient

import server.api.routes.pokemon as pokemon_routes
from server.api.dependencies import (
    get_llm_service,
    get_pokemon_service,
    get_query_builder,
)
from server.api.schemas.pokemon import (
    PokemonSearchResult,
    Retrieval,
    SearchResult,
)
from server.main import app


def test_explain_endpoint_returns_an_llm_explanation():
    pokemon_document = "Lapras\n\nCharacteristics: gentle and calm."

    class PokemonService:
        def get_pokemon_by_id(self, pokemon_id):
            assert pokemon_id == "131"
            return pokemon_document

    class QueryBuilder:
        def build_query(self, traits, note):
            assert [trait.value for trait in traits] == ["calm", "protective"]
            assert note == "For a quiet home."
            return "Characteristics: calm and protective."

    class LLMService:
        def explain_pokemon_match(self, query, document):
            assert query == "Characteristics: calm and protective."
            assert document == pokemon_document
            return "Lapras is a gentle and protective companion."

    app.dependency_overrides = {
        get_pokemon_service: PokemonService,
        get_query_builder: QueryBuilder,
        get_llm_service: LLMService,
    }
    try:
        with TestClient(app, base_url="http://localhost") as client:
            response = client.request(
                "POST",
                "/explain",
                json={
                    "searchRequest": {
                        "traits": ["calm", "protective"],
                        "note": "For a quiet home.",
                    },
                    "pokemon_id": "131",
                },
            )
    finally:
        app.dependency_overrides = {}

    assert response.status_code == 200
    assert response.json() == {
        "explanation": "Lapras is a gentle and protective companion."
    }


def test_search_endpoint_returns_results_and_the_rerank_retry_header(monkeypatch):
    monkeypatch.setattr(pokemon_routes, "enforce_search_rate_limit", lambda _: None)

    class PokemonService:
        def search_pokemon(self, query):
            assert query == "Characteristics: calm and protective."
            return SearchResult(
                pokemon=[
                    PokemonSearchResult(
                        id="131",
                        name="Lapras",
                        sprite_url="lapras.png",
                    )
                ],
                retrieval=Retrieval(
                    reranked=False,
                    rerank_unavailable_reason="rate_limited",
                    retry_after_seconds=42,
                ),
            )

    class QueryBuilder:
        def build_query(self, traits, note):
            assert [trait.value for trait in traits] == ["calm", "protective"]
            assert note is None
            return "Characteristics: calm and protective."

    app.dependency_overrides = {
        get_pokemon_service: PokemonService,
        get_query_builder: QueryBuilder,
    }
    try:
        with TestClient(app, base_url="http://localhost") as client:
            response = client.post(
                "/search",
                json={"traits": ["calm", "protective"]},
            )
    finally:
        app.dependency_overrides = {}

    assert response.status_code == 200
    assert response.headers["Retry-After"] == "42"
    assert response.json() == {
        "pokemon": [{"id": "131", "name": "Lapras", "sprite_url": "lapras.png"}],
        "retrieval": {
            "reranked": False,
            "rerank_unavailable_reason": "rate_limited",
            "retry_after_seconds": 42,
        },
    }
