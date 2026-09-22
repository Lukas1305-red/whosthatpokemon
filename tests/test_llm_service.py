from types import SimpleNamespace

import server.services.llm_service as llm_service_module
from prompts import EXPLAIN_POKEMON_MATCH_SYSTEM_PROMPT
from server.api.errors import AIProviderUnavailableError
from server.services.llm_service import LLMService


class FakeAnthropicClient:
    def __init__(self):
        self.messages = self
        self.request: dict | None = None

    def create(self, **kwargs):
        self.request = kwargs
        return SimpleNamespace(
            content=[SimpleNamespace(text="Lapras is a gentle match.")]
        )


def test_explain_pokemon_match_sends_the_query_and_document_to_anthropic():
    client = FakeAnthropicClient()

    explanation = LLMService(client).explain_pokemon_match(
        query="Characteristics: calm and protective.",
        pokemon_document="Lapras\n\nCharacteristics: gentle and seeks companionship.",
    )

    assert explanation == "Lapras is a gentle match."
    assert client.request == {
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": 200,
        "system": EXPLAIN_POKEMON_MATCH_SYSTEM_PROMPT,
        "messages": [
            {
                "role": "user",
                "content": (
                    "<search_query>\nCharacteristics: calm and protective.\n</search_query>\n\n"
                    "<pokemon_document>\nLapras\n\nCharacteristics: gentle and seeks companionship.\n"
                    "</pokemon_document>"
                ),
            }
        ],
    }


def test_explain_pokemon_match_hides_anthropic_failure_details(monkeypatch):
    class ProviderFailure(Exception):
        pass

    class FailingClient:
        def __init__(self):
            self.messages = self

        def create(self, **kwargs):
            raise ProviderFailure("provider returned a secret diagnostic")

    monkeypatch.setattr(llm_service_module, "AnthropicError", ProviderFailure)

    try:
        LLMService(FailingClient()).explain_pokemon_match("calm", "Lapras")
    except AIProviderUnavailableError as error:
        assert error.message == "The AI explanation service is temporarily unavailable."
        assert "secret" not in error.message
    else:
        raise AssertionError("Expected a provider failure to be converted safely")
