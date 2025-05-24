# Standard library imports
from typing import Optional, TypeVar

# Third-party imports
from sqlalchemy.orm import Session

# Local application imports
from app.core.storage import StorageType
from app.db.models import BaseModelWithId, LeadDB, LeadStatus
from app.models.lead import LeadCreate, LeadUpdate

from .base import BaseRepository

# Create a new type variable that's bound to BaseModelWithId
T = TypeVar("T", bound=BaseModelWithId)
ModelType = TypeVar("ModelType", bound=BaseModelWithId)


class LeadRepository(BaseRepository[LeadDB, LeadCreate, LeadUpdate]):
    """Repository for Lead operations.

    This class provides methods for interacting with Lead records in the database.
    """

    """Repository for Lead operations."""

    def __init__(self, db: Session) -> None:
        """Initialize the LeadRepository.

        Args:
            db: The database session.
        """
        # Use the actual LeadDB class
        super().__init__(LeadDB, db)

    def get_by_email(self, email: str) -> Optional[LeadDB]:
        """Get a lead by email.

        Args:
            email: The email address to search for.

        Returns:
            The LeadDB instance if found, None otherwise.
        """
        return self.db.query(LeadDB).filter(LeadDB.email == email).first()

    def create_with_resume(
        self,
        *,
        obj_in: LeadCreate,
        resume_path: Optional[str] = None,
        resume_original_filename: Optional[str] = None,
        resume_mime_type: Optional[str] = None,
        resume_size: Optional[int] = None,
    ) -> LeadDB:
        """Create a new lead with resume information.

        Args:
            obj_in: The lead creation data.
            resume_path: Path to the resume file.
            resume_original_filename: Original filename of the resume.
            resume_mime_type: MIME type of the resume file.
            resume_size: Size of the resume file in bytes.

        Returns:
            The created LeadDB instance.
        """
        obj_in_data = obj_in.dict()

        # Ensure status is properly typed
        status = obj_in_data.pop("status", None)
        if status is not None and not isinstance(status, LeadStatus):
            status = LeadStatus(status)

        db_obj = LeadDB(
            **obj_in_data,
            status=status or LeadStatus.PENDING,
            resume_path=resume_path,
            resume_original_filename=resume_original_filename,
            resume_mime_type=resume_mime_type,
            resume_size=resume_size,
        )

        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def update_resume(
        self,
        *,
        db_obj: LeadDB,
        resume_path: Optional[str] = None,
        resume_original_filename: Optional[str] = None,
        resume_mime_type: Optional[str] = None,
        resume_size: Optional[int] = None,
    ) -> LeadDB:
        """Update resume information for a lead.

        Args:
            db_obj: The lead to update.
            resume_path: New path to the resume file.
            resume_original_filename: New original filename of the resume.
            resume_mime_type: New MIME type of the resume file.
            resume_size: New size of the resume file in bytes.

        Returns:
            The updated LeadDB instance.
        """
        if resume_path is not None:
            db_obj.resume_path = resume_path
        if resume_original_filename is not None:
            db_obj.resume_original_filename = resume_original_filename
        if resume_mime_type is not None:
            db_obj.resume_mime_type = resume_mime_type
        if resume_size is not None:
            db_obj.resume_size = resume_size

        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj
