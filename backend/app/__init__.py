"""
Alma API application package.
"""

# Standard library imports
import logging
import os

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

# Configure logging
logger = logging.getLogger(__name__)

# Create FastAPI app instance
app = FastAPI(
    title="Alma API",
    description="Backend API for the Alma application",
    version=__version__,
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

# Run Alembic migrations programmatically
try:
    from alembic import command
    from alembic.config import Config

    # Get the directory containing alembic.ini
    alembic_ini_path = os.path.join(os.path.dirname(__file__), "..", "alembic.ini")

    # Create Alembic config and set the script location
    alembic_cfg = Config(alembic_ini_path)

    # Run migrations
    command.upgrade(alembic_cfg, "head")
    logger.info("Database migrations applied successfully")
except Exception as e:
    logger.error(f"Error applying database migrations: {e}")
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
