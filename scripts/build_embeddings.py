from config import settings
from dependencies import embedding_client


def parse_pokemon_to_document(pokemon: dict) -> str:

    def construct_stat_trait_string() -> str:
        stat_traits = pokemon["stat_traits"]

        if not stat_traits:
            return ""

        return f"Physical capabilities: {', '.join(stat_traits)}"

    parts = [
        pokemon["name"].title(),
        f"Characteristics: {pokemon['flavor_text']}",
        construct_stat_trait_string(),
    ]

    return "\n\n".join(part for part in parts if part)


def embed_documents(documents: list[str]) -> list[list[float]]:
    response = embedding_client.embed(
        texts=documents,
        model=settings.cohere_embedding_model,
        input_type="search_document",
        output_dimension=settings.cohere_embedding_dimension,
        embedding_types=["float"],
    )

    return response.embeddings.float
