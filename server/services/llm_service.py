from anthropic import Anthropic

from prompts import EXPLAIN_POKEMON_MATCH_SYSTEM_PROMPT


class LLMService:
    def __init__(self, llm_client: Anthropic):
        self.llm_client = llm_client

    def explain_pokemon_match(
        self,
        query: str,
        pokemon_document: str,
    ) -> str:
        response = self.llm_client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=200,
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
