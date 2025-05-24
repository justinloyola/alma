# Standard library imports
import logging
import os
from typing import Awaitable, Callable, Dict

# Third-party imports
from fastapi import Depends, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from starlette.types import Receive, Scope, Send

# Import the FastAPI app instance after all other imports to avoid circular imports
# This needs to be after the imports that the app module depends on
from app import app  # noqa: E402
from app.api import deps
from app.api.endpoints import router as api_router  # noqa: E402

# Local application imports
from app.core.config import settings
from app.core.logging_config import setup_logging

# Initialize logging
setup_logging()
logger = logging.getLogger(__name__)

# Create uploads directory if it doesn't exist
os.makedirs("uploads/resumes", exist_ok=True)


# Define a type for the ASGI application callable
ASGIAppCallable = Callable[[Scope, Receive, Send], Awaitable[None]]


@app.middleware("http")
async def log_requests(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
    """
    Log all incoming requests and responses.

    Args:
        request: The incoming request.
        call_next: The next middleware or route handler.

    Returns:
        Response: The response from the next middleware or route handler.
    """
    # Log request details
    logger.info(f"Request: {request.method} {request.url}")
    logger.debug(f"Request headers: {dict(request.headers)}")

    # Log database connection status
    try:
        from app.db.database import engine

        with engine.connect() as conn:
            conn.execute("SELECT 1")
            logger.debug("Database connection check: SUCCESS")
    except Exception as db_error:
        logger.error(f"Database connection check FAILED: {str(db_error)}", exc_info=True)

    try:
        response = await call_next(request)
        logger.info(f"Response: {request.method} {request.url} - Status: {response.status_code}")
        return response
    except Exception as e:
        logger.error(
            f"Error processing request {request.method} {request.url}: {str(e)}",
            exc_info=True,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error"},
        )


# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Trusted Host Middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"],  # In production, replace with your domain
)

# Mount static files for uploaded resumes
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


# Include the auth router without authentication
from app.api.endpoints import auth as auth_router

app.include_router(auth_router.router, prefix="/api/v1/auth", tags=["auth"])

# Include the main API router with the /api/v1 prefix and authentication
app.include_router(api_router, prefix="/api/v1", dependencies=[Depends(deps.get_current_active_user)])


@app.get("/api/v1/health", status_code=status.HTTP_200_OK, tags=["health"])
async def health_check() -> Dict[str, str]:
    """
    Health check endpoint.

    Returns:
        dict: A dictionary with the health status.
    """
    return {"status": "ok"}


@app.get("/", include_in_schema=False)
async def read_root() -> Dict[str, str]:
    """
    Root endpoint.

    Returns:
        dict: A welcome message.
    """
    return {"message": "Welcome to the Alma API"}
