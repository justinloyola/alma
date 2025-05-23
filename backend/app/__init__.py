"""
Alma API application package.
"""

# Standard library imports
import logging

# Third-party imports
from fastapi import FastAPI

from app.api import deps  # noqa: F401
from app.api.endpoints import router as api_router

# Local application imports
from app.core.config import settings
from app.db import models  # noqa: F401
from app.db.database import engine
from app.db.declarative_base import Base
from app.db.models import LeadDB, UserDB  # noqa: F401
from app.models.lead import LeadStatus  # noqa: F401
from app.models.user import User  # noqa: F401

__version__ = "0.1.0"

# Create FastAPI app instance
app = FastAPI(
    title="Alma API",
    description="Backend API for the Alma application",
    version=__version__,
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

# Initialize database tables (for development only)
# Note: In production, you should use migrations instead
try:
    Base.metadata.create_all(bind=engine)
except Exception:
    logger = logging.getLogger(__name__)
    logger.exception("Error initializing database")
    raise

# Include the API router with the /api/v1 prefix
app.include_router(api_router, prefix="/api/v1")

# Export commonly used components
__all__ = [
    "app",
    "settings",
    "deps",
    "Base",
    "engine",
    "models",
    "UserDB",
    "LeadDB",
]
