"""Safe, consistent error responses for failures in external AI services."""

from collections.abc import Mapping

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class AIProviderUnavailableError(Exception):
    """An upstream AI provider could not complete a request.

    The original exception is deliberately kept out of the response: provider
    messages may reveal credentials, request contents, or implementation details.
    """

    def __init__(
        self,
        message: str = "The AI search service is temporarily unavailable.",
        *,
        retry_after_seconds: int | None = None,
    ):
        self.message = message
        self.retry_after_seconds = retry_after_seconds
        super().__init__(message)


def install_error_handlers(app: FastAPI):
    @app.exception_handler(AIProviderUnavailableError)
    async def ai_provider_unavailable_handler(
        request: Request, error: AIProviderUnavailableError
    ) -> JSONResponse:
        headers: Mapping[str, str] | None = None
        if error.retry_after_seconds is not None:
            headers = {"Retry-After": str(error.retry_after_seconds)}

        return JSONResponse(
            status_code=503,
            headers=headers,
            content={
                "detail": error.message,
                "error_code": "ai_provider_unavailable",
                "request_id": getattr(request.state, "request_id", None),
            },
        )
