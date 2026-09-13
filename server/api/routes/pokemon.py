from api.schemas.pokemon import SearchRequest
from fastapi import APIRouter

pokemon_router = APIRouter(tags=["Pokemon"])

@pokemon_router.get("/search")
async def search_pokemon(request: SearchRequest):
  pass