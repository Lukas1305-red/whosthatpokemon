import logging
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from config import settings
from dependencies import chroma_db_client
from server.api.errors import install_error_handlers
from server.api.router import router as api_router

logging.basicConfig(
    level=settings.log_level.upper(),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Pokémon Finder for Jobs",
)

if settings.host_allowlist:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.host_allowlist)

if settings.cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "X-Request-ID"],
        expose_headers=["Retry-After", "X-Request-ID"],
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


@app.middleware("http")
async def reject_oversized_requests(request: Request, call_next):
    """Reject clearly oversized requests before request parsing or provider calls."""
    content_length = request.headers.get("content-length")
    try:
        declared_size = int(content_length) if content_length else 0
    except ValueError:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": "Invalid Content-Length header."},
        )

    if declared_size > settings.max_request_body_bytes:
        return JSONResponse(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            content={"detail": "Request body is too large."},
        )
    return await call_next(request)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/ready")
def ready():
    """Readiness is intentionally local: it never invokes paid AI providers."""
    try:
        chroma_db_client.heartbeat()
        chroma_db_client.get_collection("pokemon")
    except Exception as error:
        logger.exception("Chroma readiness check failed.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Search index is unavailable.",
        ) from error

    return {"status": "ready"}
