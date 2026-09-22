import hashlib
import json

from anthropic import Anthropic

from config import settings
from prompts import EXPLAIN_POKEMON_MATCH_SYSTEM_PROMPT
from server.services.explanation_cache import ExplanationCache

EXPLAIN_MODEL = "claude-haiku-4-5-20251001"
EXPLAIN_MAX_TOKENS = 200


class LLMService:
    def __init__(
        self,
        llm_client: Anthropic,
        explanation_cache: ExplanationCache | None = None,
    ):
        self.llm_client = llm_client
        self.explanation_cache = explanation_cache

    def explain_pokemon_match(
        self,
        query: str,
        pokemon_document: str,
    ) -> str:
        if self.explanation_cache is None:
            return self._generate_explanation(query, pokemon_document)

        return self.explanation_cache.get_or_create(
            self._cache_key(query, pokemon_document),
            lambda: self._generate_explanation(query, pokemon_document),
        )

    def _generate_explanation(self, query: str, pokemon_document: str) -> str:
        response = self.llm_client.messages.create(
            model=EXPLAIN_MODEL,
            max_tokens=EXPLAIN_MAX_TOKENS,
            system=EXPLAIN_POKEMON_MATCH_SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"<search_query>\n{query}\n</search_query>\n\n"
                        f"<pokemon_document>\n{pokemon_document}\n</pokemon_document>"
                    ),
                }
            ],
        )
        return response.content[0].text

    @staticmethod
    def _cache_key(query: str, pokemon_document: str) -> str:
        """Hash every response-affecting input without retaining it in the key."""
        cache_input = {
            "kind": "pokemon-explanation",
            "prompt_version": settings.explain_prompt_version,
            "prompt": EXPLAIN_POKEMON_MATCH_SYSTEM_PROMPT,
            "model": EXPLAIN_MODEL,
            "max_tokens": EXPLAIN_MAX_TOKENS,
            "query": query,
            "pokemon_document": pokemon_document,
        }
        serialized = json.dumps(cache_input, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()
