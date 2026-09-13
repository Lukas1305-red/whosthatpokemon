from config import settings
from dependencies import chroma_db_client, embedding_client

COLLECTION_NAME = "pokemon"


def test_pokemon_database():
    chroma_db_client.heartbeat()
    collection = chroma_db_client.get_collection(COLLECTION_NAME)

    assert collection.count() == 1024

    results = collection.get(
        limit=5,
        include=["documents", "metadatas"],
    )

    assert len(results["documents"]) == 5
    assert len(results["metadatas"]) == 5


def test_chroma_is_alive():
    assert chroma_db_client.heartbeat() is not None


def test_chroma_can_query():
    collection = chroma_db_client.get_collection("pokemon")

    response = embedding_client.embed(
        texts=["a fast and powerful fighter"],
        model=settings.cohere_embedding_model,
        input_type="search_query",
        output_dimension=settings.cohere_embedding_dimension,
        embedding_types=["float"],
    )

    results = collection.query(
        query_embeddings=[response.embeddings.float[0]],
        n_results=1,
    )

    assert len(results["ids"]) == 1
    assert len(results["ids"][0]) == 1
