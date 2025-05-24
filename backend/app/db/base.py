"""Database base classes and utilities."""

from contextlib import contextmanager
from typing import Generator, Iterator

from sqlalchemy.orm import Session

# Import the engine and SessionLocal from database.py
from .database import SessionLocal
from .declarative_base import Base, BaseModelWithId

# Re-export for backward compatibility
__all__ = ["Base", "BaseModelWithId", "get_db", "get_db_session"]


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function that yields a database session.

    Yields:
        Session: A SQLAlchemy database session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_session() -> Iterator[Session]:
    """
    Context manager for database sessions.

    Yields:
        Session: A SQLAlchemy database session.

    Raises:
        Exception: Any exception that occurs during the session.
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()
