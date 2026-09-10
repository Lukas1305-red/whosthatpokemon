from anthropic import Anthropic

from prompts import SUMMARIZE_FLAVOR_TEXTS_SYSTEM_PROMPT


def summarize_flavour_texts(
    client: Anthropic, pokemon_name: str, flavour_texts: list[str]
) -> str:

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=300,
        cache_control={"type": "ephemeral"},
        system=SUMMARIZE_FLAVOR_TEXTS_SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"Pokemon: {pokemon_name} - Flavour Texts: {flavour_texts}",
            }
        ],
    )
    return response.content[0].text
