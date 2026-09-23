from fastapi.testclient import TestClient

import server.main as main_module
from config import Settings


def test_deployment_settings_parse_comma_separated_origins_and_hosts():
    settings = Settings(
        anthropic_api_key="test",
        cohere_api_key="test",
        allowed_origins="https://app.example.com, http://localhost:3000",
        trusted_hosts="api.example.com, *.example.com",
    )

    assert settings.cors_origins == [
        "https://app.example.com",
        "http://localhost:3000",
    ]
    assert settings.host_allowlist == ["api.example.com", "*.example.com"]


def test_health_endpoint_is_live_without_checking_dependencies():
    with TestClient(main_module.app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readiness_endpoint_checks_the_chroma_collection(monkeypatch):
    class ChromaClient:
        def heartbeat(self):
            return 1

        def get_collection(self, name):
            assert name == "pokemon"
            return object()

    monkeypatch.setattr(main_module, "chroma_db_client", ChromaClient())

    with TestClient(main_module.app) as client:
        response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}
