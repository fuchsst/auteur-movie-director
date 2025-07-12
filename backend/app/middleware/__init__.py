"""
Middleware initialization and setup.
"""

from fastapi import FastAPI

from app.middleware.cors import setup_cors
from app.middleware.errors import setup_error_handlers
from app.middleware.logging import setup_logging_middleware


def setup_middleware(app: FastAPI) -> None:
    """Setup all middleware for the application"""
    setup_cors(app)
    setup_logging_middleware(app)
    setup_error_handlers(app)
