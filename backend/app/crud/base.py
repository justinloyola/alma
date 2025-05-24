from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy import inspect
from sqlalchemy.orm import InstrumentedAttribute, Session

from app.db.base import Base

# Type variables for generic CRUD operations
ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        """
        CRUD object with default methods to Create, Read, Update, Delete (CRUD).

        **Parameters**

        * `model`: A SQLAlchemy model class
        * `schema`: A Pydantic model (schema) class
        """
        self.model = model
        # Verify that the model has an 'id' attribute
        if not hasattr(model, "id") and not any(
            isinstance(attr, InstrumentedAttribute) and attr.key == "id" for attr in inspect(model).attrs
        ):
            raise ValueError(f"Model {model.__name__} must have an 'id' column")

    def get(self, db: Session, id: Any) -> Optional[ModelType]:
        """Get a single record by ID.

        Args:
            db: Database session
            id: ID of the record to retrieve

        Returns:
            The model instance if found, None otherwise
        """
        return db.query(self.model).filter(self.model.id == id).first()

    def get_multi(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """Get multiple records with pagination.

        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of model instances
        """
        return db.query(self.model).offset(skip).limit(limit).all()

    def create(self, db: Session, *, obj_in: CreateSchemaType) -> ModelType:
        """Create a new record.

        Args:
            db: Database session
            obj_in: Pydantic model or dict with data to create

        Returns:
            The created model instance
        """
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data)  # type: ignore[call-arg]
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self,
        db: Session,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]],
    ) -> ModelType:
        """Update a record.

        Args:
            db: Database session
            db_obj: The database object to update
            obj_in: Pydantic model or dict with data to update

        Returns:
            The updated model instance
        """
        obj_data = jsonable_encoder(db_obj)
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)

        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])

        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, *, id: int) -> Optional[ModelType]:
        """Remove a record by ID.

        Args:
            db: Database session
            id: ID of the record to remove

        Returns:
            The removed model instance if found, None otherwise
        """
        obj = db.query(self.model).get(id)
        if obj is None:
            return None

        db.delete(obj)
        db.commit()
        return obj
