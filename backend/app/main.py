# Standard library imports
import logging
import os
from typing import Awaitable, Callable, Dict

# Third-party imports
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from starlette.types import Receive, Scope, Send

# Local application imports
from app.api.endpoints import router as api_router
from app.core.logging_config import setup_logging
from app.db.base import Base, engine

# Initialize logging
setup_logging()
logger = logging.getLogger(__name__)

# Create database tables
Base.metadata.create_all(bind=engine)

# Create uploads directory if it doesn't exist
os.makedirs("uploads/resumes", exist_ok=True)

app = FastAPI(
    title="Alma API",
    description="Backend API for the Alma application",
    version="0.1.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    on_startup=[],
    on_shutdown=[],
)


# Define a type for the ASGI application callable
ASGIAppCallable = Callable[[Scope, Receive, Send], Awaitable[None]]


@app.middleware("http")
async def log_requests(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """
    Log all incoming requests and responses.

    Args:
        request: The incoming request.
        call_next: The next middleware or route handler.

    Returns:
        Response: The response from the next middleware or route handler.
    """
    logger.info(f"Request: {request.method} {request.url}")
    try:
        response = await call_next(request)
        logger.info(
            f"Response: {request.method} {request.url} - Status: {response.status_code}"
        )
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
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
    ],  # React and Vite dev servers
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


# Include API router
app.include_router(api_router, prefix="/api")


@app.get("/api/health", status_code=status.HTTP_200_OK, tags=["health"])
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
