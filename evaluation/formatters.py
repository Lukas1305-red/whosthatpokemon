from anthropic import Anthropic

from prompts import FORMAT_RECRUITER_QUERY_SYSTEM_PROMPT


class AnthropicQueryFormatter:
    """Optional LLM query transform used for offline experiments."""

    def __init__(self, client: Anthropic, model: str = "claude-haiku-4-5-20251001"):
        self.client = client
        self.model = model

    def __call__(self, query: str) -> str:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=120,
            system=FORMAT_RECRUITER_QUERY_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": query}],
        )
        return response.content[0].text.strip()
