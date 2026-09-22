from types import SimpleNamespace

from cohere.core.api_error import ApiError
from fastapi.testclient import TestClient

import server.services.pokemon_service as pokemon_service_module
from server.api.dependencies import get_pokemon_service, get_query_builder
from server.main import app
from server.services.pokemon_service import PokemonService


def test_embedding_provider_failure_returns_safe_503_response(monkeypatch):
    class FailingCohereClient:
        def embed(self, **kwargs):
            raise ApiError(status_code=500, body={"message": "secret provider detail"})

    class PokemonRepository:
        def search(self, embedding, top_k):
            raise AssertionError("repository should not be called")

    class QueryBuilder:
        def build_query(self, traits, note):
            return "calm"

    monkeypatch.setattr(
        pokemon_service_module, "embedding_client", FailingCohereClient()
    )
    monkeypatch.setattr(
        pokemon_service_module, "enforce_cohere_embed_rate_limit", lambda: None
    )
    app.dependency_overrides = {
        get_pokemon_service: lambda: PokemonService(PokemonRepository()),
        get_query_builder: QueryBuilder,
    }
    try:
        with TestClient(app) as client:
            response = client.post("/search", json={"traits": ["calm"]})
    finally:
        app.dependency_overrides = {}

    assert response.status_code == 503
    assert (
        response.json()["detail"] == "The AI search service is temporarily unavailable."
    )
    assert response.json()["error_code"] == "ai_provider_unavailable"
    assert response.json()["request_id"] == response.headers["X-Request-ID"]
    assert "secret provider detail" not in response.text


def test_rerank_fallback_does_not_hide_non_rate_limit_http_errors(monkeypatch):
    class Repository:
        def search(self, embedding, top_k):
            return {
                "ids": [["1"]],
                "metadatas": [[{"name": "Bulbasaur", "sprite": "sprite.png"}]],
                "documents": [["calm"]],
            }

    class Client:
        def embed(self, **kwargs):
            return SimpleNamespace(embeddings=SimpleNamespace(float=[[0.1]]))

    monkeypatch.setattr(pokemon_service_module, "embedding_client", Client())
    monkeypatch.setattr(
        pokemon_service_module, "enforce_cohere_embed_rate_limit", lambda: None
    )

    from fastapi import HTTPException

    def invalid_rerank_configuration():
        raise HTTPException(status_code=500)

    monkeypatch.setattr(
        pokemon_service_module,
        "enforce_cohere_rerank_rate_limit",
        invalid_rerank_configuration,
    )

    try:
        PokemonService(Repository()).search_pokemon("calm", top_k=1)
    except HTTPException as error:
        assert error.status_code == 500
    else:
        raise AssertionError("Expected the non-rate-limit error to propagate")


def test_rerank_auth_failure_is_not_silently_degraded(monkeypatch):
    class Repository:
        def search(self, embedding, top_k):
            return {
                "ids": [["1"]],
                "metadatas": [[{"name": "Bulbasaur", "sprite": "sprite.png"}]],
                "documents": [["calm"]],
            }

    class Client:
        def embed(self, **kwargs):
            return SimpleNamespace(embeddings=SimpleNamespace(float=[[0.1]]))

        def rerank(self, **kwargs):
            raise ApiError(status_code=401)

    monkeypatch.setattr(pokemon_service_module, "embedding_client", Client())
    monkeypatch.setattr(
        pokemon_service_module, "enforce_cohere_embed_rate_limit", lambda: None
    )
    monkeypatch.setattr(
        pokemon_service_module, "enforce_cohere_rerank_rate_limit", lambda: None
    )

    from server.api.errors import AIProviderUnavailableError

    try:
        PokemonService(Repository()).search_pokemon("calm", top_k=1)
    except AIProviderUnavailableError:
        pass
    else:
        raise AssertionError(
            "Expected the Cohere authentication failure to be surfaced"
        )
