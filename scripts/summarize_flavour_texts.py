import json
from pathlib import Path

from anthropic import Anthropic

from dependencies import anthropic_client
from prompts import SUMMARIZE_FLAVOR_TEXTS_SYSTEM_PROMPT

OUTPUT_PATH = Path("data/pokemon.json")

def summarize_flavour_texts(client: Anthropic, pokemon_name: str, flavour_texts: list[str]) -> str:

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
    ]
  )
  return response.content[0].text


def summarize_flavour_texts_for_all_pokemon():
  results = []
  with open("data/pokemon_raw.json") as pokemon_json_file:
    pokemon_raw_dict = json.load(pokemon_json_file)  
    for pokemon in pokemon_raw_dict[:3]:

      response = summarize_flavour_texts(
        client=anthropic_client,
        pokemon_name=pokemon["name"],
        flavour_texts=pokemon["flavor_texts"]
      )

      pokemon.pop("flavor_texts")
      pokemon["flavor_text"] = response

      results.append(pokemon)

  OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
  with open(OUTPUT_PATH, "w") as f:
    f.write(json.dumps(results, indent=2, ensure_ascii=False))
    print(f"\n✓ saved {len(results)} pokemon to {OUTPUT_PATH}")


if __name__ == "__main__":
  summarize_flavour_texts_for_all_pokemon()