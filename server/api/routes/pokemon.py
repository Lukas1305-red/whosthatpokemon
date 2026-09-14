from fastapi import APIRouter, Depends, Request

from server.api.dependencies import get_pokemon_service
from server.api.rate_limit import enforce_search_rate_limit
from server.api.schemas.pokemon import SearchRequest, SearchResponse

pokemon_router = APIRouter(tags=["Pokemon"])


@pokemon_router.get("/search")
async def search_pokemon(
    http_request: Request,
    request: SearchRequest,
    service=Depends(get_pokemon_service),  # noqa: B008
):
    enforce_search_rate_limit(http_request)
    query = request.query
    result = service.search_pokemon(query)
    return SearchResponse(pokemon=result)
