"""Database models and session management."""

from typing import TypeVar

# Import models to ensure they are registered with SQLAlchemy
# This must be done before creating any database sessions
from . import models  # noqa: F401
from .base import get_db, get_db_session
from .database import SQLALCHEMY_DATABASE_URI, SessionLocal, engine

# Import base classes and utilities
from .declarative_base import Base, BaseModelWithId
from .models import LeadDB, LeadStatus, UserDB  # noqa: F401

# Re-export commonly used types and models
__all__ = [
    # Base classes
    "Base",
    "BaseModelWithId",
    # Database connection
    "SessionLocal",
    "engine",
    "get_db",
    "get_db_session",
    "SQLALCHEMY_DATABASE_URI",
    # Models
    "models",
    "LeadDB",
    "UserDB",
    # Enums
    "LeadStatus",
]

# Type variables for generic model types
ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=dict)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=dict)
