import json

from build_embeddings import embed_documents, parse_pokemon_to_document
from tqdm import tqdm

from dependencies import chroma_db_client

COLLECTION_NAME = "pokemon"
POKEMON_SOURCE_PATH = "data/pokemon_enriched.json"

BATCH_SIZE = 20


def populate_db():
    def get_metadata_from_pokemon(pokemon: dict) -> dict:
        return {
            "types": pokemon["types"],
            "height": pokemon["height"],
            "weight": pokemon["weight"],
            "generation": pokemon["generation"],
            "is_starter": pokemon["is_starter"],
            "is_legendary": pokemon["is_legendary"],
            "is_mythical": pokemon["is_mythical"],
            "sprite": pokemon["sprite"],
        }

    try:
        collection = chroma_db_client.create_collection(name=COLLECTION_NAME)

        with open(POKEMON_SOURCE_PATH) as pokemon_json:
            pokemon_dict = json.load(pokemon_json)
            for i in tqdm(
                range(0, len(pokemon_dict), BATCH_SIZE), desc="Embedding Pokemon"
            ):
                batch = pokemon_dict[i : i + BATCH_SIZE]
                documents = [parse_pokemon_to_document(pokemon) for pokemon in batch]
                embeddings = embed_documents(documents)
                for pokemon, document, embedding in zip(
                    batch,
                    documents,
                    embeddings,
                ):
                    collection.add(
                        ids=[str(pokemon["id"])],
                        documents=[document],
                        embeddings=[embedding],
                        metadatas=[get_metadata_from_pokemon(pokemon)],
                    )

            print(f"Successfully populated '{COLLECTION_NAME}'.")
    except FileNotFoundError:
        print(
            f"The file {POKEMON_SOURCE_PATH} doesn't exist. Run make enrich first to create enriched pokemon data"
        )


if __name__ == "__main__":
    populate_db()
