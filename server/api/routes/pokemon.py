from fastapi import APIRouter, Depends, Request, Response

from server.api.dependencies import get_pokemon_service, get_query_builder
from server.api.rate_limit import enforce_search_rate_limit
from server.api.schemas.pokemon import SearchRequest, SearchResponse

pokemon_router = APIRouter(tags=["Pokemon"])


@pokemon_router.get("/search")
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
