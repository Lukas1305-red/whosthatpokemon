from uuid import uuid4

from fastapi import FastAPI, Request

from server.api.errors import install_error_handlers
from server.api.router import router as api_router

app = FastAPI(
    title="Pokémon Finder for Jobs",
)

install_error_handlers(app)
app.include_router(api_router)


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Attach a correlation id without trusting a client-supplied identifier."""
    request.state.request_id = uuid4().hex
    response = await call_next(request)
    response.headers["X-Request-ID"] = request.state.request_id
    return response


@app.get("/health")
def health():
    return {"status": "ok"}
