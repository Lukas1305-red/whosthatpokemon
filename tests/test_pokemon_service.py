from types import SimpleNamespace

from cohere.core.api_error import ApiError

import server.services.pokemon_service as pokemon_service_module
from server.services.pokemon_service import PokemonService


class FakeRepository:
    def search(self, embedding, top_k):
        assert embedding == [0.1, 0.2]
        assert top_k == 25
        return {
            "ids": [["1", "2", "3"]],
            "metadatas": [
                [
                    {"name": "Bulbasaur", "sprite": "bulbasaur.png"},
                    {"name": "Charmander", "sprite": "charmander.png"},
                    {"name": "Squirtle", "sprite": "squirtle.png"},
                ]
            ],
            "documents": [["patient", "brave", "careful"]],
        }


class FakeCohereClient:
    def embed(self, **kwargs):
        assert kwargs["texts"] == ["patient and careful"]
        return SimpleNamespace(embeddings=SimpleNamespace(float=[[0.1, 0.2]]))

    def rerank(self, **kwargs):
        assert kwargs["query"] == "patient and careful"
        assert kwargs["documents"] == ["patient", "brave", "careful"]
        assert kwargs["top_n"] == 2
        return SimpleNamespace(
            results=[
                SimpleNamespace(index=2, relevance_score=0.9),
                SimpleNamespace(index=0, relevance_score=0.8),
            ]
        )


def test_search_pokemon_reranks_vector_candidates(monkeypatch):
    monkeypatch.setattr(pokemon_service_module, "embedding_client", FakeCohereClient())

    results = PokemonService(FakeRepository()).search_pokemon(
        "patient and careful", top_k=2
    )

    assert [result.name for result in results] == ["Squirtle", "Bulbasaur"]


def test_search_pokemon_falls_back_to_raw_order_when_reranking_fails(monkeypatch):
    class RateLimitedCohereClient(FakeCohereClient):
        def rerank(self, **kwargs):
            raise ApiError(status_code=429)

    monkeypatch.setattr(
        pokemon_service_module, "embedding_client", RateLimitedCohereClient()
    )

    results = PokemonService(FakeRepository()).search_pokemon(
        "patient and careful", top_k=2
    )

    assert [result.name for result in results] == ["Bulbasaur", "Charmander"]
