# Standard library imports
from typing import Optional

# Third-party imports
from sqlalchemy.orm import Session

# Local application imports
from app.db.models import LeadDB
from app.models.lead import LeadCreate, LeadUpdate
from .base import BaseRepository

class LeadRepository(BaseRepository[LeadDB, LeadCreate, LeadUpdate]):
    def __init__(self, db: Session):
        super().__init__(LeadDB, db)
    
    def get_by_email(self, email: str) -> Optional[LeadDB]:
        """Get a lead by email."""
        return self.db.query(LeadDB).filter(LeadDB.email == email).first()
    
    def create_with_resume(
        self, 
        *, 
        obj_in: LeadCreate, 
        resume_path: Optional[str] = None,
        resume_original_filename: Optional[str] = None,
        resume_mime_type: Optional[str] = None,
        resume_size: Optional[int] = None,
        resume_storage_type: str = "filesystem"
    ) -> LeadDB:
        """Create a new lead with resume information."""
        db_obj = LeadDB(
            **obj_in.dict(exclude={"resume_path"}),
            resume_path=resume_path,
            resume_original_filename=resume_original_filename,
            resume_mime_type=resume_mime_type,
            resume_size=resume_size,
            resume_storage_type=resume_storage_type
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
        resume_storage_type: Optional[str] = None
    ) -> LeadDB:
        """Update resume information for a lead."""
        if resume_path is not None:
            db_obj.resume_path = resume_path
        if resume_original_filename is not None:
            db_obj.resume_original_filename = resume_original_filename
        if resume_mime_type is not None:
            db_obj.resume_mime_type = resume_mime_type
        if resume_size is not None:
            db_obj.resume_size = resume_size
        if resume_storage_type is not None:
            db_obj.resume_storage_type = resume_storage_type
            
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj
