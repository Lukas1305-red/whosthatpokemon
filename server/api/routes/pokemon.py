from fastapi import APIRouter, Depends

from server.api.dependencies import get_pokemon_service
from server.api.schemas.pokemon import SearchRequest, SearchResponse

pokemon_router = APIRouter(tags=["Pokemon"])


@pokemon_router.get("/search")
async def search_pokemon(request: SearchRequest, service=Depends(get_pokemon_service)):  # noqa: B008
    query = request.query
    result = service.search_pokemon(query)
    return SearchResponse(pokemon=result)
