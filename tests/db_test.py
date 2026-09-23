from server.repositories.pokemon_repository import PokemonRepository


class FakeCollection:
    def __init__(self) -> None:
        self.query_calls: list[dict] = []
        self.get_calls: list[dict] = []
        self.query_result = {
            "ids": [["25"]],
            "documents": [["Pikachu: quick and friendly."]],
            "metadatas": [[{"name": "Pikachu"}]],
        }
        self.get_result = {
            "ids": ["25"],
            "documents": ["Pikachu: quick and friendly."],
        }

    def query(self, **kwargs):
        self.query_calls.append(kwargs)
        return self.query_result

    def get(self, **kwargs):
        self.get_calls.append(kwargs)
        return self.get_result


class FakeChromaClient:
    def __init__(self, collection: FakeCollection) -> None:
        self.collection = collection
        self.collection_names: list[str] = []

    def get_collection(self, name: str) -> FakeCollection:
        self.collection_names.append(name)
        return self.collection


def test_pokemon_repository_searches_the_pokemon_collection():
    collection = FakeCollection()
    repository = PokemonRepository(FakeChromaClient(collection))

    result = repository.search([0.1, 0.2], top_k=5)

    assert result == collection.query_result
    assert collection.query_calls == [
        {"query_embeddings": [[0.1, 0.2]], "n_results": 5}
    ]


def test_pokemon_repository_returns_a_document_for_a_known_id():
    collection = FakeCollection()
    repository = PokemonRepository(FakeChromaClient(collection))

    result = repository.get_by_id("25")

    assert result == "Pikachu: quick and friendly."
    assert collection.get_calls == [{"ids": ["25"], "include": ["documents"]}]


def test_pokemon_repository_returns_none_for_an_unknown_id():
    collection = FakeCollection()
    collection.get_result = {"ids": [], "documents": []}
    repository = PokemonRepository(FakeChromaClient(collection))

    assert repository.get_by_id("missing") is None
