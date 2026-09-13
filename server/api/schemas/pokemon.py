from pydantic import BaseModel


class SearchRequest(BaseModel):
    query: str


class PokemonSearchResult(BaseModel):
    id: str
    name: str
    sprite_url: str


class SearchResponse(BaseModel):
    pokemon: list[PokemonSearchResult]
