from fastapi import FastAPI

app = FastAPI(
    title="Pokémon Finder for Jobs",
)


@app.get("/health")
def health():
    return {"status": "ok"}