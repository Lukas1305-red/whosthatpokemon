from fastapi import APIRouter

from server.api.routes.pokemon import pokemon_router

router = APIRouter()

router.include_router(pokemon_router)
