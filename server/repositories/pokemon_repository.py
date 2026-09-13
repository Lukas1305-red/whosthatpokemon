from chromadb import QueryResult
from chromadb.api import ClientAPI


class PokemonRepository:
    def __init__(self, chroma_client: ClientAPI):
        self.chroma_client = chroma_client

    def search(self, embedding: list[float], top_k: int = 5) -> QueryResult:
        collection = self.chroma_client.get_collection("pokemon")

        return collection.query(
            query_embeddings=[embedding],
            n_results=top_k,
        )
