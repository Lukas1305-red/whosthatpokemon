from typing import Literal

from pydantic import BaseModel


class SearchRequest(BaseModel):
    query: str


class PokemonSearchResult(BaseModel):
    id: str
    name: str
    sprite_url: str


class Retrieval(BaseModel):
    reranked: bool
    rerank_unavailable_reason: Literal["rate_limited", "cohere_error"] | None = None
    retry_after_seconds: int | None = None


class SearchResult(BaseModel):
    pokemon: list[PokemonSearchResult]
    retrieval: Retrieval


class SearchResponse(BaseModel):
    pokemon: list[PokemonSearchResult]
    retrieval: Retrieval
