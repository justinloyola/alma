"""SQLAlchemy declarative base and base model classes."""
from datetime import datetime
from typing import Any, Dict, Optional, TypeVar

from sqlalchemy import DateTime, Integer, event
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql import func

# Create a type variable for the base class
T = TypeVar("T", bound="BaseModelWithId")


# Create a base class for declarative models
class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    pass


class BaseModelWithId(Base):
    """Base model that includes common columns like id, created_at, and updated_at."""

    __abstract__ = True

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert the model instance to a dictionary."""
        return {
            column.name: getattr(self, column.name) for column in self.__table__.columns
        }

    def update(self, **kwargs: Any) -> None:
        """Update model attributes.

        Args:
            **kwargs: Attributes to update with their new values.
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)


# Add event listeners
@event.listens_for(BaseModelWithId, "before_update")
def receive_before_update(mapper, connection, target):
    """Update the updated_at timestamp before updating a record."""
    target.updated_at = func.now()


@event.listens_for(BaseModelWithId, "before_insert")
def receive_before_insert(mapper, connection, target):
    """Set the created_at timestamp before inserting a new record."""
    target.created_at = func.now()
    target.updated_at = func.now()
