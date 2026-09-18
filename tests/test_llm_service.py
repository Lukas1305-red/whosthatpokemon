from types import SimpleNamespace

from prompts import EXPLAIN_POKEMON_MATCH_SYSTEM_PROMPT
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
        pokemon_name="Lapras",
        pokemon_document="Lapras is gentle and seeks companionship.",
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
                    "<pokemon_name>Lapras</pokemon_name>\n\n"
                    "<pokemon_document>\nLapras is gentle and seeks companionship.\n"
                    "</pokemon_document>"
                ),
            }
        ],
    }
