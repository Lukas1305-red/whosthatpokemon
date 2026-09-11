from dependencies import chroma_db_client

COLLECTION_NAME = "pokemon"


def test_pokemon_database():
    collection = chroma_db_client.get_collection(COLLECTION_NAME)

    assert collection.count() == 1024

    results = collection.get(
        limit=5,
        include=["documents", "metadatas"],
    )

    assert len(results["documents"]) == 5
    assert len(results["metadatas"]) == 5
