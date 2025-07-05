"""
Error handling middleware.
"""

import logging
from datetime import datetime
from typing import Union

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import AppException

logger = logging.getLogger(__name__)


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Handle application exceptions"""
    request_id = getattr(request.state, "request_id", "unknown")

    logger.error(
        f"Application error: {exc.message}",
        extra={
            "request_id": request_id,
            "error_code": exc.code,
            "details": exc.details,
        },
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            **exc.to_dict(),
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat(),
        },
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle validation exceptions"""
    request_id = getattr(request.state, "request_id", "unknown")

    logger.error(
        "Validation error",
        extra={
            "request_id": request_id,
            "errors": exc.errors(),
        },
    )

    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": {"errors": exc.errors()},
            },
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat(),
        },
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Handle HTTP exceptions"""
    request_id = getattr(request.state, "request_id", "unknown")

    logger.error(
        f"HTTP error: {exc.detail}",
        extra={
            "request_id": request_id,
            "status_code": exc.status_code,
        },
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {"code": f"HTTP_{exc.status_code}", "message": exc.detail, "details": {}},
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat(),
        },
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle generic exceptions"""
    request_id = getattr(request.state, "request_id", "unknown")

    logger.exception(
        "Unhandled exception",
        extra={
            "request_id": request_id,
        },
    )

    # Don't leak sensitive information
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An internal server error occurred",
                "details": {},
            },
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat(),
        },
    )


def setup_error_handlers(app: FastAPI) -> None:
    """Setup error handlers"""
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
