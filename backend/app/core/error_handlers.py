"""
FastAPI error handlers ensuring consistent and safe error responses.
Prevents leaking filesystem paths, stack traces, and internal variables.
"""
import uuid
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.app.core.exceptions import LegalRAGException
from backend.app.core.logging import logger


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(LegalRAGException)
    async def legal_rag_exception_handler(request: Request, exc: LegalRAGException) -> JSONResponse:
        correlation_id = str(uuid.uuid4())
        logger.warning(
            f"Domain exception [{exc.error_code}] on {request.method} {request.url.path} "
            f"(correlation_id={correlation_id}): {exc.message}"
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error_code": exc.error_code,
                "message": exc.message,
                "correlation_id": correlation_id,
                "details": exc.details,
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        correlation_id = str(uuid.uuid4())
        logger.info(f"Validation error on {request.method} {request.url.path} (correlation_id={correlation_id})")
        # Sanitize details to avoid leaking sensitive client inputs
        errors = [
            {"field": ".".join(str(loc) for loc in err["loc"]), "issue": err["msg"]}
            for err in exc.errors()
        ]
        return JSONResponse(
            status_code=422,
            content={
                "error_code": "VALIDATION_ERROR",
                "message": "The request payload failed schema validation.",
                "correlation_id": correlation_id,
                "details": {"validation_errors": errors},
            },
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        correlation_id = str(uuid.uuid4())
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error_code": f"HTTP_{exc.status_code}",
                "message": exc.detail,
                "correlation_id": correlation_id,
                "details": {},
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        correlation_id = str(uuid.uuid4())
        logger.error(
            f"Unhandled server error on {request.method} {request.url.path} "
            f"(correlation_id={correlation_id}): {type(exc).__name__}"
        )
        # Note: Do not return str(exc) to client to avoid leaking paths or secrets
        return JSONResponse(
            status_code=500,
            content={
                "error_code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected server error occurred. Please contact support with the correlation ID.",
                "correlation_id": correlation_id,
                "details": {},
            },
        )
