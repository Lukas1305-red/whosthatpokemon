from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class PokemonTrait(Enum):
    RELIABLE = "reliable"
    INDEPENDENT = "independent"
    CALM = "calm"
    CURIOUS = "curious"
    PROTECTIVE = "protective"
    ADAPTABLE = "adaptable"


class SearchRequest(BaseModel):
    traits: list[PokemonTrait] = Field(min_length=1, max_length=4)
    note: str | None = Field(default=None, max_length=150)

    @field_validator("traits")
    @classmethod
    def traits_must_be_unique(cls, traits: list[PokemonTrait]) -> list[PokemonTrait]:
        if len(traits) != len(set(traits)):
            raise ValueError("traits must not contain duplicates")
        return traits


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


class ExplainRequest(BaseModel):
    searchRequest: SearchRequest
    pokemon_id: str


class ExplainResponse(BaseModel):
    explanation: str
