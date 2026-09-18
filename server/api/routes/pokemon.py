from fastapi import APIRouter, Depends, HTTPException, Request, Response

from server.api.dependencies import (
    get_llm_service,
    get_pokemon_service,
    get_query_builder,
)
from server.api.rate_limit import enforce_explain_rate_limit, enforce_search_rate_limit
from server.api.schemas.pokemon import (
    ExplainRequest,
    ExplainResponse,
    SearchRequest,
    SearchResponse,
)

pokemon_router = APIRouter(tags=["Pokemon"])


@pokemon_router.post("/search")
async def search_pokemon(
    http_request: Request,
    response: Response,
    request: SearchRequest,
    pokemon_service=Depends(get_pokemon_service),  # noqa: B008
    query_builder=Depends(get_query_builder),  # noqa: B008
):
    enforce_search_rate_limit(http_request)
    note = request.note
    traits = request.traits
    query = query_builder.build_query(traits, note)
    result = pokemon_service.search_pokemon(query)
    if result.retrieval.retry_after_seconds is not None:
        response.headers["Retry-After"] = str(result.retrieval.retry_after_seconds)
    return SearchResponse(pokemon=result.pokemon, retrieval=result.retrieval)


@pokemon_router.post("/explain")
async def explain_pokemon_choice(
    http_request: Request,
    request: ExplainRequest,
    pokemon_service=Depends(get_pokemon_service),  # noqa: B008
    query_builder=Depends(get_query_builder),  # noqa: B008
    llm_service=Depends(get_llm_service),  # noqa: B008
):
    enforce_explain_rate_limit(http_request)
    pokemon_id = request.pokemon_id

    pokemon = pokemon_service.get_pokemon_by_id(pokemon_id)

    if not pokemon:
        raise HTTPException(
            status_code=404,
            detail=f"Pokémon with ID {pokemon_id} was not found.",
        )

    original_search_request = request.searchRequest

    traits = original_search_request.traits
    note = original_search_request.note

    query = query_builder.build_query(traits, note)

    explanation = llm_service.explain_pokemon_match(query, pokemon)

    return ExplainResponse(explanation=explanation)
