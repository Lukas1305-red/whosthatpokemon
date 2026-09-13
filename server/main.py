from api.router import router as api_router
from fastapi import FastAPI

app = FastAPI(
    title="Pokémon Finder for Jobs",
)

app.include_router(api_router)


@app.get("/health")
def health():
    return {"status": "ok"}
