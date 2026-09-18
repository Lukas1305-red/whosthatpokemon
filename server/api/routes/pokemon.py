from fastapi import APIRouter, Depends, Request, Response

from server.api.dependencies import get_pokemon_service
from server.api.rate_limit import enforce_search_rate_limit
from server.api.schemas.pokemon import SearchRequest, SearchResponse

pokemon_router = APIRouter(tags=["Pokemon"])


@pokemon_router.get("/search")
async def search_pokemon(
    http_request: Request,
    response: Response,
    request: SearchRequest,
    service=Depends(get_pokemon_service),  # noqa: B008
):
    enforce_search_rate_limit(http_request)
    note = request.note
    # TODO: Change this to using
    result = service.search_pokemon(note)
    if result.retrieval.retry_after_seconds is not None:
        response.headers["Retry-After"] = str(result.retrieval.retry_after_seconds)
    return SearchResponse(pokemon=result.pokemon, retrieval=result.retrieval)
