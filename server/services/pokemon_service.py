from config import settings
from dependencies import embedding_client
from server.api.schemas.pokemon import PokemonSearchResult
from server.repositories.pokemon_repository import PokemonRepository


class PokemonService:
    def __init__(self, repo: PokemonRepository):
        self.repo = repo

    def search_pokemon(self, query: str) -> list[PokemonSearchResult]:
        embedded_query = embedding_client.embed(
            texts=[query],
            model=settings.cohere_embedding_model,
            input_type="search_query",
            output_dimension=settings.cohere_embedding_dimension,
            embedding_types=["float"],
        )

        result = self.repo.search(embedded_query.embeddings.float[0])
        return [
            PokemonSearchResult(
                id=id_,
                name=metadata["name"],
                sprite_url=metadata["sprite"],
            )
            for id_, metadata in zip(
                result["ids"][0],
                result["metadatas"][0],
            )
        ]
