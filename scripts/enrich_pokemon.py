import json
from pathlib import Path

from dependencies import anthropic_client
from scripts.deterministic_pokemon_enrichment import create_stat_traits
from scripts.llm_based_pokemon_enrichment import summarize_flavour_texts

OUTPUT_PATH = Path("data/pokemon_enriched.json")

def enrich_all_pokemon():
    results = []
    with open("data/pokemon_raw.json") as pokemon_json_file:
        pokemon_raw_dict = json.load(pokemon_json_file)
        for pokemon in pokemon_raw_dict[:1]:
            response = summarize_flavour_texts(
                client=anthropic_client,
                pokemon_name=pokemon["name"],
                flavour_texts=pokemon["flavor_texts"],
            )

            pokemon.pop("flavor_texts")
            pokemon["flavor_text"] = response

            stat_traits = create_stat_traits(pokemon["stats"])
            pokemon["stat_traits"] = stat_traits

            results.append(pokemon)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        f.write(json.dumps(results, indent=2, ensure_ascii=False))
        print(f"\n✓ saved {len(results)} pokemon to {OUTPUT_PATH}")


if __name__ == "__main__":
  enrich_all_pokemon()
