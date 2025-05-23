# Standard library imports
from typing import Any, Dict, Optional

# Third-party imports
from fastapi import HTTPException, UploadFile
from fastapi import status as http_status
from sqlalchemy.orm import Session

# Local application imports
from app.db.models import LeadDB
from app.models.lead import LeadCreate, LeadStatus, LeadUpdate
from app.repositories.lead import LeadRepository


class LeadService:
    def __init__(self, db: Session):
        self.repository = LeadRepository(db)

    def get_lead(self, lead_id: int) -> Optional[LeadDB]:
        """Get a lead by ID."""
        return self.repository.get(lead_id)

    def get_leads(self, skip: int = 0, limit: int = 100) -> list[LeadDB]:
        """Get multiple leads with pagination."""
        return self.repository.get_multi(skip=skip, limit=limit)

    async def create_lead(
        self,
        lead_data: Dict[str, Any],
        resume_file: Optional[UploadFile] = None,
        storage_type: str = "filesystem",
    ) -> LeadDB:
        """
        Create a new lead with optional resume file.

        Args:
            lead_data: Lead data including first_name, last_name, email
            resume_file: Optional resume file to upload
            storage_type: Storage type for the resume ('filesystem' or 'postgres')

        Returns:
            The created lead

        Raises:
            HTTPException: If email already exists or file upload fails
        """
        # Check for duplicate email
        if self.repository.get_by_email(lead_data["email"]):
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "Duplicate email",
                    "details": "A lead with this email already exists",
                },
            )

        # Create lead without resume first
        lead = self.repository.create(obj_in=LeadCreate(**lead_data))

        # Handle resume upload if provided
        if resume_file:
            try:
                # Save the file and update lead with file info
                lead = self.repository.update_resume(
                    db_obj=lead,
                    resume_storage_type=storage_type,
                    resume_original_filename=resume_file.filename,
                    resume_mime_type=resume_file.content_type,
                    resume_size=resume_file.size,
                )

            except Exception as e:
                # If file upload fails, delete the lead and re-raise
                self.repository.delete(id=lead.id)
                raise HTTPException(
                    status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail={"error": "Error saving resume", "details": str(e)},
                )

        return lead

    def update_lead(self, lead_id: int, lead_update: LeadUpdate) -> Optional[LeadDB]:
        """Update a lead."""
        lead = self.get_lead(lead_id)
        if not lead:
            return None

        return self.repository.update(db_obj=lead, obj_in=lead_update)

    def delete_lead(self, lead_id: int) -> bool:
        """Delete a lead."""
        lead = self.get_lead(lead_id)
        if not lead:
            return False

        self.repository.delete(id=lead_id)
        return True

    def update_lead_status(self, lead_id: int, status: str) -> LeadDB:
        """
        Update a lead's status.

        Args:
            lead_id: ID of the lead to update
            status: New status (must be a valid LeadStatus value)

        Returns:
            The updated lead

        Raises:
            HTTPException: If lead is not found or status is invalid
        """
        lead = self.get_lead(lead_id)
        if not lead:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=f"Lead with id {lead_id} not found",
            )

        # Validate the status
        valid_statuses = [s.value for s in LeadStatus]
        if status not in valid_statuses:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}",
            )

        # Update the status
        update_data = {"status": status}
        return self.repository.update(db_obj=lead, obj_in=update_data)
