from config import settings
from dependencies import embedding_client
from server.repositories.pokemon_repository import PokemonRepository


class PokemonService:
    def __init__(self, repo: PokemonRepository):
        self.repo = repo

    def search_pokemon(self, query: str):
        embedded_query = embedding_client.embed(
            texts=[query],
            model=settings.cohere_embedding_model,
            input_type="search_query",
            output_dimension=settings.cohere_embedding_dimension,
            embedding_types=["float"],
        )

        return self.repo.search(embedded_query.embeddings.float[0])
