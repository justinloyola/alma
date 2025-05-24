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
    import logging

    # Configure SQLAlchemy logging
    logging.basicConfig()
    logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.pool").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.orm").setLevel(logging.INFO)

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
                echo_pool="debug",  # Log connection pool events
                logging_name="sqlalchemy.engine",
                pool_pre_ping=True,  # Enable connection health checks
                pool_recycle=3600,  # Recycle connections after 1 hour
            )
        else:
            return create_engine(
                uri,
                pool_pre_ping=True,
                pool_size=10,
                max_overflow=20,
                echo=True,
                echo_pool="debug",
                logging_name="sqlalchemy.engine",
            )
    return create_engine(uri, echo=True, echo_pool="debug")


# Create database engine
engine = create_db_engine()

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Scoped session factory for use in web applications
SessionScoped = scoped_session(SessionLocal)

# Export the database URL for use in migrations
SQLALCHEMY_DATABASE_URI = str(engine.url)
