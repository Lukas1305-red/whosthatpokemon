import hashlib
import json
import logging

from anthropic import Anthropic, AnthropicError, RateLimitError

from config import settings
from prompts import EXPLAIN_POKEMON_MATCH_SYSTEM_PROMPT
from server.api.errors import AIProviderUnavailableError
from server.services.explanation_cache import ExplanationCache

EXPLAIN_MODEL = "claude-haiku-4-5-20251001"
EXPLAIN_MAX_TOKENS = 200

logger = logging.getLogger(__name__)


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
        try:
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
        except RateLimitError as error:
            logger.warning(
                "Anthropic explanation request was rate-limited.", exc_info=True
            )
            raise AIProviderUnavailableError(
                "The AI explanation service is temporarily unavailable.",
                retry_after_seconds=self._retry_after_seconds(error),
            ) from error
        except AnthropicError as error:
            logger.exception(
                "Anthropic explanation request failed (%s).", type(error).__name__
            )
            raise AIProviderUnavailableError(
                "The AI explanation service is temporarily unavailable."
            ) from error

        return response.content[0].text

    @staticmethod
    def _retry_after_seconds(error: RateLimitError) -> int | None:
        retry_after = error.response.headers.get("Retry-After")
        try:
            return max(1, int(retry_after)) if retry_after else None
        except ValueError:
            return None

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
