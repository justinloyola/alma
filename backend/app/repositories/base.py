# Standard library imports
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

# Third-party imports
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy import Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column


# Define a base class that enforces the id column
class BaseModelWithId(DeclarativeBase):
    """Base model that enforces the presence of an id column."""

    __abstract__ = True

    # Use mapped_column for better type support
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)


# Define type variables for the repository
ModelType = TypeVar("ModelType", bound=BaseModelWithId)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType], db: Session):
        """
        Base repository with default CRUD operations.

        Args:
            model: SQLAlchemy model class
            db: Database session
        """
        self.model = model
        self.db = db

    def get(self, id: Any) -> Optional[ModelType]:
        """Get a single record by ID.

        Args:
            id: The ID of the record to retrieve.

        Returns:
            The model instance if found, None otherwise.
        """
        return self.db.query(self.model).filter(self.model.id == id).first()

    def get_multi(self, *, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """Get multiple records with pagination.

        Args:
            skip: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            A list of model instances.
        """
        return self.db.query(self.model).offset(skip).limit(limit).all()

    def create(self, *, obj_in: CreateSchemaType) -> ModelType:
        """Create a new record.

        Args:
            obj_in: The data to create the record with.

        Returns:
            The created model instance.
        """
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def update(self, *, db_obj: ModelType, obj_in: Union[UpdateSchemaType, Dict[str, Any]]) -> ModelType:
        """Update a record.

        Args:
            db_obj: The database object to update.
            obj_in: The data to update the record with.

        Returns:
            The updated model instance.
        """
        obj_data = jsonable_encoder(db_obj)
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)

        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])

        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def delete(self, *, id: int) -> Optional[ModelType]:
        """Delete a record by ID.

        Args:
            id: The ID of the record to delete.

        Returns:
            The deleted model instance, or None if not found.

        Raises:
            ValueError: If the record with the given ID is not found.
        """
        # Get the object to delete
        obj = self.db.query(self.model).get(id)
        if obj is None:
            return None

        # Create a new instance of the same class
        obj_dict = {c.name: getattr(obj, c.name) for c in obj.__table__.columns}
        obj_copy = self.model(**obj_dict)

        # Delete the original object
        self.db.delete(obj)
        self.db.commit()

        return obj_copy
