# Standard library imports
import logging
from typing import List

# Third-party imports
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

# Local application imports
from app.core.storage import get_storage
from app.db.deps import get_db
from app.models.lead import Lead, LeadUpdate, LeadStatus, LeadBase
from app.services.lead import LeadService

# Set up logging
logger = logging.getLogger(__name__)

# Create a router for leads endpoints
router = APIRouter(prefix="/leads", tags=["leads"])

@router.post("", response_model=Lead, status_code=status.HTTP_201_CREATED)
async def create_new_lead(
    background_tasks: BackgroundTasks,
    first_name: str = Form(..., min_length=1, max_length=100),
    last_name: str = Form(..., min_length=1, max_length=100),
    email: str = Form(..., pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'),
    resume: UploadFile = File(..., description="Resume file (PDF, JPG, or PNG, max 5MB)"),
    storage_type: str = Form("filesystem", description="Storage type: 'filesystem' or 'postgres'"),
    db: Session = Depends(get_db)
):
    """
    Create a new lead with resume upload.
    
    - **first_name**: Lead's first name (required, 1-100 chars)
    - **last_name**: Lead's last name (required, 1-100 chars)
    - **email**: Lead's email address (required, valid email format)
    - **resume**: Resume file (PDF or image, max 5MB)
    - **storage_type**: Storage type for the resume ('filesystem' or 'postgres')
    """
    try:
        logger.info("Received new lead submission", extra={
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "storage_type": storage_type,
            "action": "submit_lead",
            "status": "started"
        })
        
        # Create lead data
        lead_data = {
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "status": LeadStatus.PENDING
        }
        
        # Use the LeadService to handle lead creation and file upload
        lead_service = LeadService(db)
        lead = await lead_service.create_lead(lead_data, resume_file=resume, storage_type=storage_type)
        
        logger.info("Successfully created lead with resume", extra={
            "lead_id": lead.id,
            "email": email,
            "storage_type": storage_type,
            "action": "submit_lead",
            "status": "completed"
        })
        
        return lead
        
    except HTTPException as he:
        logger.warning("HTTP exception in create_new_lead", 
            extra={
                "email": email,
                "action": "submit_lead",
                "status": "failed",
                "status_code": he.status_code,
                "detail": he.detail
            }
        )
        raise
        
    except Exception as e:
        logger.error("Unexpected error in create_new_lead", 
            exc_info=True,
            extra={
                "email": email,
                "action": "submit_lead",
                "status": "failed",
                "error": str(e),
                "error_type": e.__class__.__name__
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Internal server error", "details": str(e)}
        )

@router.get("", response_model=List[Lead])
def read_leads(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db)
):
    """
    Retrieve all leads with pagination.
    
    - **skip**: Number of records to skip (default: 0)
    - **limit**: Maximum number of records to return (default: 100)
    """
    lead_service = LeadService(db)
    return lead_service.get_leads(skip=skip, limit=limit)

@router.get("/{lead_id}", response_model=Lead)
def read_lead(
    lead_id: int, 
    db: Session = Depends(get_db)
):
    """
    Retrieve a specific lead by ID.
    
    - **lead_id**: ID of the lead to retrieve
    """
    lead_service = LeadService(db)
    lead = lead_service.get_lead(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead

@router.get("/{lead_id}/resume")
async def download_resume(
    lead_id: int,
    db: Session = Depends(get_db)
):
    """
    Download a lead's resume.
    
    - **lead_id**: ID of the lead whose resume to download
    """
    lead_service = LeadService(db)
    lead = lead_service.get_lead(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    # Check if lead has a resume
    if not lead.resume_path:
        raise HTTPException(status_code=404, detail="No resume found for this lead")
    
    # Get the appropriate storage backend
    try:
        storage = get_storage(lead.resume_storage_type or "filesystem")
        file_obj = await storage.get_file(lead)
        
        if not file_obj:
            raise HTTPException(status_code=404, detail="Resume file not found")
            
        # Return the file
        return StreamingResponse(
            file_obj,
            media_type=lead.resume_mime_type or "application/octet-stream",
            headers={
                "Content-Disposition": f"attachment; filename={lead.resume_original_filename or 'resume'}",
                "Content-Length": str(lead.resume_size) if lead.resume_size else None
            }
        )
        
    except Exception as e:
        logger.error(f"Error retrieving resume: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": "Error retrieving resume", "details": str(e)}
        )

@router.put("/{lead_id}", response_model=Lead)
def update_lead(
    lead_id: int,
    lead_update: LeadUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a lead's information.
    
    - **lead_id**: ID of the lead to update
    - **lead_update**: Fields to update (all optional)
    """
    lead_service = LeadService(db)
    updated_lead = lead_service.update_lead(lead_id, lead_update)
    if not updated_lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return updated_lead

@router.put("/{lead_id}/reached-out", response_model=Lead)
def mark_lead_reached_out(
    lead_id: int,
    db: Session = Depends(get_db)
):
    """
    Mark a lead as reached out.
    
    - **lead_id**: ID of the lead to mark as reached out
    """
    lead_service = LeadService(db)
    try:
        lead = lead_service.update_lead_status(lead_id, LeadStatus.REACHED_OUT)
        return lead
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error marking lead as reached out: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Internal server error", "details": str(e)}
        )

@router.delete("/{lead_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_lead(
    lead_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a lead.
    
    - **lead_id**: ID of the lead to delete
    """
    lead_service = LeadService(db)
    if not lead_service.delete_lead(lead_id):
        raise HTTPException(status_code=404, detail="Lead not found")
    return None
