# Standard library imports
import logging
from io import BytesIO
from typing import List, Optional

# Third-party imports
try:
    import magic

    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
    Response,
)
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

# Local application imports
from app.core.storage import StorageType, get_storage
from app.db.base import get_db
from app.db.models import LeadDB, LeadStatus as DBLeadStatus
from app.models.lead import Lead, LeadCreate, LeadUpdate, LeadStatus

# Set up logging
logger = logging.getLogger(__name__)


def safe_lead_status(status_value: Optional[str]) -> LeadStatus:
    """Safely convert a status string to LeadStatus.

    Args:
        status_value: The status value to convert

    Returns:
        LeadStatus: The converted status, defaults to PENDING if invalid
    """
    if not status_value:
        return LeadStatus.PENDING

    try:
        # Try to convert the status value to uppercase and match with enum
        upper_status = status_value.upper()
        if upper_status in [e.value.upper() for e in LeadStatus]:
            return LeadStatus[upper_status]

        # Handle legacy status values
        if upper_status == "NEW":
            return LeadStatus.PENDING

    except (ValueError, KeyError, AttributeError):
        pass

    # Default to PENDING if conversion fails
    return LeadStatus.PENDING


# Create a router for leads endpoints
router = APIRouter(prefix="/leads", tags=["leads"])


@router.post("", response_model=Lead, status_code=status.HTTP_201_CREATED)
async def create_new_lead(
    background_tasks: BackgroundTasks,
    first_name: str = Form(..., min_length=1, max_length=100),
    last_name: str = Form(..., min_length=1, max_length=100),
    email: str = Form(..., pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"),
    resume: UploadFile = File(
        ...,
        description="Resume file (PDF, JPG, or PNG, max 5MB)",
    ),
    storage_type: str = Form(
        "filesystem", description="Storage type: 'filesystem' or 'postgres'"
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
    existing_lead = db.query(LeadDB).filter(LeadDB.email == email).first()
    if existing_lead:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A lead with email {email} already exists",
        )

    try:
        # Create a temporary lead object for file storage
        temp_lead = LeadDB(
            first_name=first_name,
            last_name=last_name,
            email=email,
            status=LeadStatus.PENDING.value,  # Convert to string value for DB
        )

        # Get the file content and MIME type
        file_content = await resume.read()
        mime = magic.Magic(mime=True)
        mime_type = mime.from_buffer(file_content)

        # Save the uploaded file
        storage_type_enum = (
            StorageType(storage_type) if storage_type else StorageType.FILESYSTEM
        )
        storage = get_storage(storage_type_enum)

        # Create a file-like object from the uploaded file content
        file_obj = BytesIO(file_content)

        # Save the file using the storage backend
        file_path = await storage.save_file(
            file_data=file_obj,
            lead=temp_lead,
            original_filename=resume.filename or "resume",
            mime_type=mime_type,
        )

        # Prepare file info for the response
        file_info = {
            "file_path": file_path,
            "original_filename": resume.filename,
            "content_type": mime_type,
            "size": len(file_content),
        }

        # Create lead in database
        lead_data = LeadCreate(
            first_name=first_name,
            last_name=last_name,
            email=email,
            status=LeadStatus.PENDING,  # This uses the Pydantic model's enum
        )

        # Create lead data dictionary
        lead_dict = lead_data.dict(exclude_unset=True)

        # Ensure file_info is a dictionary
        file_info_dict = (
            dict(file_info) if not isinstance(file_info, dict) else file_info
        )

        # Create the database model with additional resume fields
        db_lead = LeadDB(
            first_name=lead_dict["first_name"],
            last_name=lead_dict["last_name"],
            email=lead_dict["email"],
            status=lead_dict.get("status", LeadStatus.PENDING),
            resume_path=file_info_dict.get("file_path"),
            resume_original_filename=file_info_dict.get("original_filename"),
            resume_mime_type=file_info_dict.get("content_type"),
            resume_size=file_info_dict.get("size"),
            resume_storage_type=StorageType(storage_type)
            if storage_type
            else StorageType.FILESYSTEM,
        )
        db.add(db_lead)
        db.commit()
        db.refresh(db_lead)

        logger.info("Successfully created lead with ID: %s", db_lead.id)

        # Add background task if needed
        if background_tasks:
            logger.debug("Adding background task for new lead processing")
            # background_tasks.add_task(process_new_lead, db_lead.id)

        # Create a new Lead instance with the required fields
        lead = Lead(
            id=db_lead.id,
            first_name=db_lead.first_name,
            last_name=db_lead.last_name,
            email=db_lead.email,
            status=LeadStatus(db_lead.status),  # Convert to the correct enum type
            created_at=db_lead.created_at,
            updated_at=db_lead.updated_at,
            resume_path=db_lead.resume_path,
            resume_original_filename=db_lead.resume_original_filename,
            resume_mime_type=db_lead.resume_mime_type,
            resume_size=db_lead.resume_size,
            resume_storage_type=db_lead.resume_storage_type,
        )
        return lead

    except ValueError as e:
        error_msg = f"Validation error: {str(e)}"
        logger.error(
            error_msg,
            exc_info=True,
            extra={
                "email": email,
                "action": "submit_lead",
                "status": "validation_failed",
            },
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg
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
            detail={"error": "Internal server error"},
        ) from e


@router.get("", response_model=List[Lead])
def read_leads(
    skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
) -> List[Lead]:
    """
    Retrieve all leads with pagination.
    """
    try:
        # Query the database
        db_leads = db.query(LeadDB).offset(skip).limit(limit).all()

        # Convert database models to Pydantic models
        leads = []
        for lead in db_leads:
            lead_dict = {
                "id": lead.id,
                "first_name": lead.first_name,
                "last_name": lead.last_name,
                "email": lead.email,
                "status": LeadStatus(lead.status)
                if lead.status
                else LeadStatus.PENDING,
                "created_at": lead.created_at,
                "updated_at": lead.updated_at,
            }

            # Add optional fields
            if hasattr(lead, "resume_path") and lead.resume_path:
                lead_dict["resume_path"] = lead.resume_path
            if (
                hasattr(lead, "resume_original_filename")
                and lead.resume_original_filename
            ):
                lead_dict["resume_original_filename"] = lead.resume_original_filename

            leads.append(Lead(**lead_dict))

        return leads

    except Exception as e:
        print(f"=== ERROR IN READ_LEADS: {str(e)}")
        print(f"=== ERROR TYPE: {type(e).__name__}")
        import traceback

        print("=== TRACEBACK ===")
        print(traceback.format_exc())
        print("================")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving leads: {str(e)}",
        )


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
    db_lead = db.query(LeadDB).filter(LeadDB.id == lead_id).first()
    if db_lead is None:
        raise HTTPException(status_code=404, detail="Lead not found")

    try:
        return Lead(
            id=db_lead.id,
            first_name=db_lead.first_name,
            last_name=db_lead.last_name,
            email=db_lead.email,
            status=LeadStatus(db_lead.status) if db_lead.status else LeadStatus.PENDING,
            created_at=db_lead.created_at,
            updated_at=db_lead.updated_at,
            resume_path=db_lead.resume_path,
            resume_original_filename=db_lead.resume_original_filename,
            resume_mime_type=db_lead.resume_mime_type,
            resume_size=db_lead.resume_size,
            resume_storage_type=db_lead.resume_storage_type.value
            if db_lead.resume_storage_type
            else None,
        )
    except Exception as e:
        logger.error(
            f"Error processing lead {lead_id}",
            exc_info=True,
            extra={"lead_id": lead_id, "error": str(e)},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing lead data",
        )


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
    db_lead = db.query(LeadDB).filter(LeadDB.id == lead_id).first()
    if not db_lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    # Check if lead has a resume
    if not db_lead.resume_path:
        raise HTTPException(status_code=404, detail="No resume found for this lead")

    # Get the appropriate storage backend
    try:
        storage_type = (
            str(db_lead.resume_storage_type)
            if db_lead.resume_storage_type
            else "filesystem"
        )
        storage = get_storage(StorageType(storage_type))
        file_obj = await storage.get_file(db_lead)
        if not file_obj:
            raise HTTPException(status_code=404, detail="Resume file not found")

        return StreamingResponse(
            file_obj,
            media_type=db_lead.resume_mime_type or "application/octet-stream",
            headers={
                "Content-Disposition": f"attachment; filename={db_lead.resume_original_filename or 'resume'}",
                "Content-Length": str(db_lead.resume_size or 0)
                if db_lead.resume_size
                else "0",
            },
        )
    except Exception as e:
        logger.error(f"Error retrieving resume: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Error retrieving resume file"
        ) from e


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
    db_lead = db.query(LeadDB).filter(LeadDB.id == lead_id).first()
    if not db_lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    update_data = lead_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_lead, key, value)

    db.commit()
    db.refresh(db_lead)
    return Lead.from_orm(db_lead)


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
    db_lead = db.query(LeadDB).filter(LeadDB.id == lead_id).first()
    if not db_lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    # Update the status using the database model's enum
    db_lead.status = DBLeadStatus.REACHED_OUT
    db.commit()
    db.refresh(db_lead)
    return Lead.from_orm(db_lead)


@router.delete("/{lead_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_lead(lead_id: int, db: Session = Depends(get_db)) -> Response:
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
    db_lead = db.query(LeadDB).filter(LeadDB.id == lead_id).first()
    if not db_lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    db.delete(db_lead)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
