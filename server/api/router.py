from api.routes.pokemon import pokemon_router
from fastapi import APIRouter

router = APIRouter()

router.include_router(pokemon_router)

