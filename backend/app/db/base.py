import os
from contextlib import contextmanager
from typing import Generator, Iterator

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

load_dotenv()

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./alma.db")

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Base class for all database models.

    This class provides the base functionality for all SQLAlchemy models.
    It's a thin wrapper around SQLAlchemy's DeclarativeBase.
    """


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
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
