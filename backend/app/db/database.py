from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import scoped_session, sessionmaker

from app.core.config import settings


def create_db_engine(database_uri: Optional[str] = None) -> Engine:
    """Create a SQLAlchemy engine with the given database URI.

    Args:
        database_uri: The database URI to connect to. If None, uses the one
            from settings.

    Returns:
        A SQLAlchemy Engine instance.

    Raises:
        ValueError: If no database URI is provided and none is set in settings.
    """
    uri = database_uri or settings.SQLALCHEMY_DATABASE_URI
    if not uri:
        raise ValueError("No database URL provided and none set in settings")

    # Convert string URL to SQLAlchemy URL object if needed
    if isinstance(uri, str):
        if uri.startswith("sqlite"):
            return create_engine(
                uri,
                connect_args={"check_same_thread": False},
                echo=True,  # Enable SQL query logging for debugging
            )
        else:
            return create_engine(
                uri,
                pool_pre_ping=True,
                pool_size=10,
                max_overflow=20,
            )
    return create_engine(uri)


# Create database engine
engine = create_db_engine()

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Scoped session factory for use in web applications
SessionScoped = scoped_session(SessionLocal)

# Export the database URL for use in migrations
SQLALCHEMY_DATABASE_URI = str(engine.url)
