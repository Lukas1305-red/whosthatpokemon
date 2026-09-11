def parse_pokemon_to_document(pokemon: dict) -> str:

    def construct_stat_trait_string() -> str:
        stat_traits = pokemon["stat_traits"]

        if not stat_traits:
            return ""

        return f"Physical capabilities: {', '.join(stat_traits)}"

    parts = [
        pokemon["name"].title(),
        f"Characteristics: {pokemon['semantic_description']}",
        construct_stat_trait_string(),
    ]

    return "\n\n".join(part for part in parts if part)
    