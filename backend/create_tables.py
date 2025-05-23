"""Script to create database tables."""

# This must be imported first to set up the Python path
import _path_setup  # noqa: F401

# Local application imports
# Import models to ensure they are registered with SQLAlchemy
from app.db import (
    database,
    models,  # noqa: F401
)
from app.db.declarative_base import Base

# Get the engine after imports
engine = database.engine


def create_tables():
    """Create all database tables."""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")


if __name__ == "__main__":
    create_tables()
