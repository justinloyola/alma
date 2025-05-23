# Standard library imports
import logging
from typing import List

# Third-party imports
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    Response,
    UploadFile,
    status,
)
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

# Local application imports
from app.core.storage import get_storage
from app.db.deps import get_db
from app.models.lead import Lead, LeadBase, LeadStatus, LeadUpdate

# Set up logging
logger = logging.getLogger(__name__)

# Create a router for leads endpoints
router = APIRouter(prefix="/leads", tags=["leads"])


@router.post("", response_model=Lead, status_code=status.HTTP_201_CREATED)
async def create_new_lead(
    background_tasks: BackgroundTasks,
    first_name: str = Form(..., min_length=1, max_length=100),
    last_name: str = Form(..., min_length=1, max_length=100),
    email: str = Form(
        ...,
        pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    ),
    resume: UploadFile = File(
        ...,
        description="Resume file (PDF, JPG, or PNG, max 5MB)",
    ),
    storage_type: str = Form(
        "filesystem",
        description="Storage type: 'filesystem' or 'postgres'"
    ),
    db: Session = Depends(get_db),
) -> Lead:
    """
    Create a new lead with resume upload.

    Args:
        background_tasks: Background tasks handler
        first_name: Lead's first name (1-100 chars)
        last_name: Lead's last name (1-100 chars)
        email: Lead's email address (valid email format)
        resume: Uploaded resume file
        storage_type: Storage type for the resume
        db: Database session

    Returns:
        The newly created lead

    Raises:
        HTTPException: If lead exists or validation fails
    """
    logger.info("Creating new lead for email: %s", email)
    
    # Check if lead with this email already exists
    existing_lead = db.query(Lead).filter(Lead.email == email).first()
    if existing_lead:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A lead with email {email} already exists",
        )
    
    try:
        # Save the uploaded file
        storage = get_storage(storage_type)
        file_info = await storage.save_file(
            file=resume,
            prefix="resumes",
            max_size_mb=5,
            allowed_types={"application/pdf", "image/jpeg", "image/png"}
        )
        
        # Create lead in database
        lead_data = LeadBase(
            first_name=first_name,
            last_name=last_name,
            email=email,
            resume_path=file_info["file_path"],
            resume_original_filename=file_info["original_filename"],
            resume_mime_type=file_info["content_type"],
            resume_size=file_info["size"],
            resume_storage_type=storage_type,
            status=LeadStatus.NEW
        )
        
        db_lead = Lead(**lead_data.dict())
        db.add(db_lead)
        db.commit()
        db.refresh(db_lead)
        
        logger.info("Successfully created lead with ID: %s", db_lead.id)
        
        # Add background task if needed
        if background_tasks:
            logger.debug("Adding background task for new lead processing")
            # background_tasks.add_task(process_new_lead, db_lead.id)
        
        return db_lead
        
    except ValueError as e:
        error_msg = f"Validation error: {str(e)}"
        logger.error(
            error_msg,
            exc_info=True,
            extra={
                "email": email,
                "action": "submit_lead",
                "status": "validation_failed"
            },
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        ) from e
    except Exception as e:
        logger.error(
            "Unexpected error creating lead",
            exc_info=True,
            extra={
                "email": email,
                "action": "submit_lead",
                "status": "failed",
                "error": str(e),
                "error_type": e.__class__.__name__,
            },
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Internal server error"}
        ) from e


@router.get("", response_model=List[Lead])
def read_leads(
    skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
) -> List[Lead]:
    """
    Retrieve all leads with pagination.

    Args:
        skip: Number of records to skip (default: 0)
        limit: Maximum number of records to return (default: 100)
        db: Database session

    Returns:
        List of lead objects
    """
    return db.query(Lead).offset(skip).limit(limit).all()


@router.get("/{lead_id}", response_model=Lead)
def read_lead(lead_id: int, db: Session = Depends(get_db)) -> Lead:
    """
    Retrieve a specific lead by ID.

    Args:
        lead_id: ID of the lead to retrieve
        db: Database session

    Returns:
        Lead object

    Raises:
        HTTPException: If lead is not found
    """
    db_lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not db_lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return db_lead


@router.get("/{lead_id}/resume")
async def download_resume(
    lead_id: int, db: Session = Depends(get_db)
) -> StreamingResponse:
    """
    Download a lead's resume.

    Args:
        lead_id: ID of the lead whose resume to download
        db: Database session

    Returns:
        Streaming response with the resume file

    Raises:
        HTTPException: If lead or resume is not found
    """
    db_lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not db_lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    # Check if lead has a resume
    if not db_lead.resume_path:
        raise HTTPException(status_code=404, detail="No resume found for this lead")

    # Get the appropriate storage backend
    try:
        storage = get_storage(db_lead.resume_storage_type or "filesystem")
        file_obj = await storage.get_file(db_lead)

        if not file_obj:
            raise HTTPException(status_code=404, detail="Resume file not found")

        # Return the file
        return StreamingResponse(
            file_obj,
            media_type=db_lead.resume_mime_type or "application/octet-stream",
            headers={
                "Content-Disposition": (
                    "attachment; "
                    f"filename={db_lead.resume_original_filename or 'resume'}"
                ),
                "Content-Length": (
                    str(db_lead.resume_size) if db_lead.resume_size else None
                ),
            },
        )

    except Exception as e:
        logger.error(f"Error retrieving resume: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": "Error retrieving resume", "details": str(e)},
        )


@router.put("/{lead_id}", response_model=Lead)
def update_lead(
    lead_id: int, lead_update: LeadUpdate, db: Session = Depends(get_db)
) -> Lead:
    """
    Update a lead's information.

    Args:
        lead_id: ID of the lead to update
        lead_update: Fields to update (all optional)
        db: Database session

    Returns:
        Updated lead object

    Raises:
        HTTPException: If lead is not found
    """
    db_lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not db_lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    update_data = lead_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_lead, key, value)
    
    db.commit()
    db.refresh(db_lead)
    return db_lead


@router.put("/{lead_id}/reached-out", response_model=Lead)
def mark_lead_reached_out(lead_id: int, db: Session = Depends(get_db)) -> Lead:
    """
    Mark a lead as reached out.

    Args:
        lead_id: ID of the lead to mark as reached out
        db: Database session

    Returns:
        Updated lead object

    Raises:
        HTTPException: If lead is not found
    """
    db_lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not db_lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    db_lead.status = LeadStatus.REACHED_OUT
    db.commit()
    db.refresh(db_lead)
    return db_lead


@router.delete("/{lead_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_lead(
    lead_id: int, db: Session = Depends(get_db)
) -> Response:
    """
    Delete a lead.

    Args:
        lead_id: ID of the lead to delete
        db: Database session

    Returns:
        Empty response with 204 status code

    Raises:
        HTTPException: If lead is not found
    """
    db_lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not db_lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    db.delete(db_lead)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
