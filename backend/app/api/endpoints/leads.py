# Standard library imports
import logging
import os
from io import BytesIO
from typing import Any, List, Optional

# Third-party imports
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    Response,
    UploadFile,
    status,
)
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.email import send_lead_notification

# Try to import magic for MIME type detection
MAGIC_AVAILABLE = False
magic_inst = None
try:
    import magic

    magic_inst = magic.Magic(mime=True)
    MAGIC_AVAILABLE = True
except (ImportError, OSError):
    # Fall back to file extension if python-magic is not available
    pass

# Local application imports
# These need to be imported after any sys.path modifications
# Import this last to avoid circular imports
from app.api.deps import get_current_user  # noqa: E402
from app.core.storage import StorageType, get_storage  # noqa: E402
from app.db.base import get_db  # noqa: E402
from app.db.models import LeadDB  # noqa: E402
from app.db.models import LeadStatus as DBLeadStatus
from app.models.lead import Lead, LeadCreate, LeadStatus, LeadUpdate  # noqa: E402

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


@router.get("/test-email")
async def test_email(request: Request):
    """
    Test endpoint to check email configuration and sending.
    """
    import os

    from fastapi.responses import JSONResponse

    # Log environment variables for debugging
    env_vars = {
        "SENDGRID_API_KEY": "***" if os.getenv("SENDGRID_API_KEY") else "NOT SET",
        "FROM_EMAIL": os.getenv("FROM_EMAIL", "NOT SET"),
        "ADMIN_EMAIL": os.getenv("ADMIN_EMAIL", "NOT SET"),
        "SMTP_HOST": os.getenv("SMTP_HOST", "NOT SET"),
        "SMTP_PORT": os.getenv("SMTP_PORT", "NOT SET"),
        "SMTP_USER": os.getenv("SMTP_USER", "NOT SET"),
        "SMTP_PASSWORD": "***" if os.getenv("SMTP_PASSWORD") else "NOT SET",
        "EMAILS_ENABLED": os.getenv("EMAILS_ENABLED", "NOT SET"),
    }

    # Try to send a test email
    try:
        from app.core.email import send_email

        test_email = os.getenv("ADMIN_EMAIL")
        if not test_email or test_email == "NOT SET":
            return JSONResponse(
                status_code=400,
                content={"status": "error", "message": "ADMIN_EMAIL is not set", "environment": env_vars},
            )

        # Send a test email
        success = await send_email(
            to_emails=[test_email],
            subject="Test Email from Alma",
            html_content="<h1>Test Email</h1><p>This is a test email from the Alma application.</p>",
        )

        if success:
            return {"status": "success", "message": f"Test email sent to {test_email}", "environment": env_vars}
        else:
            return JSONResponse(
                status_code=500,
                content={"status": "error", "message": "Failed to send test email", "environment": env_vars},
            )

    except Exception as e:
        import traceback

        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": f"Error sending test email: {str(e)}",
                "traceback": traceback.format_exc(),
                "environment": env_vars,
            },
        )


# Register the POST endpoint for creating a new lead
@router.post(
    "",
    response_model=Lead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new lead with resume upload",
    description="Create a new lead with resume upload. This endpoint is public and doesn't require authentication.",
)
async def create_lead_route(
    background_tasks: BackgroundTasks,
    first_name: str = Form(..., min_length=1, max_length=100),
    last_name: str = Form(..., min_length=1, max_length=100),
    email: str = Form(..., pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"),
    phone: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    resume: UploadFile = File(..., description="Resume file (PDF, JPG, or PNG, max 5MB)"),
    db: Session = Depends(get_db),
):
    return await create_lead(
        background_tasks=background_tasks,
        first_name=first_name,
        last_name=last_name,
        email=email,
        resume=resume,
        db=db,
    )


# Endpoint for lead submission
@router.post(
    "/",
    response_model=Lead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new lead",
    response_description="The created lead",
    include_in_schema=True,
)
async def create_lead(
    background_tasks: BackgroundTasks,
    first_name: str = Form(..., min_length=1, max_length=100),
    last_name: str = Form(..., min_length=1, max_length=100),
    email: str = Form(..., pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"),
    phone: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    resume: UploadFile = File(
        ...,
        description="Resume file (PDF, JPG, or PNG, max 5MB)",
    ),
    db: Session = Depends(get_db),
) -> Lead:
    """
    Create a new lead with resume upload.

    This endpoint is public and doesn't require authentication.
    """
    logger.info(f"[LEAD] Received new lead submission for {email}")

    try:
        # Create the lead
        result = await create_new_lead(
            background_tasks=background_tasks,
            first_name=first_name,
            last_name=last_name,
            email=email,
            resume=resume,
            db=db,
            current_user=None,  # No user for public endpoint
        )

        logger.info(f"[LEAD] Successfully processed lead for {email}")
        return result

    except HTTPException as he:
        logger.error(f"[LEAD] Error creating lead: {str(he.detail)}")
        raise
    except Exception as e:
        logger.error(f"[LEAD] Unexpected error creating lead: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing your request",
        )


@router.post("", response_model=Lead, status_code=status.HTTP_201_CREATED)
async def create_new_lead(
    background_tasks: BackgroundTasks,
    first_name: str = Form(...),
    last_name: str = Form(...),
    email: str = Form(...),
    resume: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: Optional[Any] = None,  # Optional authenticated user
) -> Lead:
    """
    Create a new lead with resume upload.

    Args:
        background_tasks: Background tasks handler
        first_name: Lead's first name (1-100 chars)
        last_name: Lead's last name (1-100 chars)
        email: Lead's email address (valid email format)
        resume: Uploaded resume file
        db: Database session

    Returns:
        The newly created lead

    Raises:
        HTTPException: If lead exists or validation fails
    """
    logger.info(f"[LEAD] Starting lead creation for {email}")

    # Check if lead with this email already exists
    existing_lead = db.query(LeadDB).filter(LeadDB.email == email).first()
    if existing_lead:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The lead with this email already exists in the system.",
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
        if MAGIC_AVAILABLE and magic_inst is not None:
            mime_type = magic_inst.from_buffer(file_content)
        else:
            # Fall back to file extension if magic is not available
            file_extension = ""
            if resume.filename and "." in resume.filename:
                file_extension = resume.filename.split(".")[-1].lower()
            mime_type = file_extension

        # Save the uploaded file using filesystem storage
        storage = get_storage(StorageType.FILESYSTEM)

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
        file_info_dict = dict(file_info) if not isinstance(file_info, dict) else file_info

        # Create the database model with additional resume fields
        db_lead = LeadDB(
            first_name=lead_dict["first_name"],
            last_name=lead_dict["last_name"],
            email=lead_dict["email"],
            status=lead_dict.get("status", LeadStatus.PENDING).value,  # Convert enum to string
            resume_path=file_info_dict.get("file_path"),
            resume_original_filename=file_info_dict.get("original_filename"),
            resume_mime_type=file_info_dict.get("content_type"),
            resume_size=file_info_dict.get("size"),
        )
        db.add(db_lead)
        db.commit()
        db.refresh(db_lead)

        logger.info("Successfully created lead with ID: %s", db_lead.id)

        # Prepare email notification data
        admin_email = os.getenv("ADMIN_EMAIL")
        logger.info("[LEAD] Email Configuration:")
        logger.info(f"[LEAD] - ADMIN_EMAIL: {admin_email}")
        logger.info(f"[LEAD] - FROM_EMAIL: {os.getenv('FROM_EMAIL')}")
        logger.info(f"[LEAD] - SENDGRID_API_KEY exists: {bool(os.getenv('SENDGRID_API_KEY'))}")

        if admin_email:
            # Prepare lead data for email
            lead_data = {
                "id": db_lead.id,
                "first_name": db_lead.first_name,
                "last_name": db_lead.last_name,
                "email": db_lead.email,
                "created_at": db_lead.created_at.isoformat() if db_lead.created_at else "Unknown",
                "status": db_lead.status,
            }

            logger.info(f"[LEAD] Sending email notification for lead ID: {db_lead.id}")

            # Import the function directly to avoid potential serialization issues
            from app.core.email import send_lead_notification

            # Create a synchronous wrapper function to run the async task
            def send_notification_task():
                import asyncio

                try:
                    logger.info(f"[LEAD] Starting email notification task for lead ID: {lead_data['id']}")
                    from app.core.email import send_lead_notification

                    # Create a new event loop for the background task
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)

                    # Run the async function
                    result = loop.run_until_complete(send_lead_notification(lead_data, [admin_email]))
                    logger.info(f"[LEAD] Email notification task completed with result: {result}")
                    return result
                except Exception as e:
                    logger.error(
                        f"[LEAD] Error in email notification task: {str(e)}",
                        exc_info=True,
                    )
                    return False
                finally:
                    # Close the loop when done
                    loop.close()

            # Add the task to background tasks
            background_tasks.add_task(send_notification_task)
            logger.info("[LEAD] Email notification task added to background tasks")
        else:
            logger.warning("[LEAD] ADMIN_EMAIL not set, skipping email notification")

        # Create a new Lead instance using from_orm to handle the conversion
        lead = Lead.from_orm(db_lead)
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
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg) from e
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


@router.get(
    "",
    response_model=List[Lead],
    summary="List all leads",
    response_description="A list of leads",
)
def read_leads(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user),
) -> List[Lead]:
    """
    Retrieve all leads with pagination.
    """
    try:
        # Query the database
        db_leads = db.query(LeadDB).offset(skip).limit(limit).all()

        # Convert database models to Pydantic models using from_orm
        leads = [Lead.from_orm(lead) for lead in db_leads]

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


@router.get(
    "/{lead_id}",
    response_model=Lead,
    summary="Get lead by ID",
    response_description="The lead with the given ID",
    responses={404: {"description": "Lead not found"}},
    dependencies=[Depends(get_current_user)],
)
def read_lead(
    lead_id: int,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user),
) -> Lead:
    """
    Retrieve a specific lead by ID.

    Args:
        lead_id: ID of the lead to retrieve
        db: Database session
        current_user: Current user making the request

    Returns:
        Lead object

    Raises:
        HTTPException: If lead is not found
    """
    db_lead = db.query(LeadDB).filter(LeadDB.id == lead_id).first()
    if db_lead is None:
        raise HTTPException(status_code=404, detail="Lead not found")

    try:
        # Convert database model to Pydantic model using from_orm
        return Lead.from_orm(db_lead)
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


@router.get(
    "/{lead_id}/resume",
    summary="Download lead's resume",
    response_description="The resume file",
    responses={
        200: {"content": {"application/octet-stream": {}}},
        404: {"description": "Lead or resume not found"},
    },
    dependencies=[Depends(get_current_user)],
)
async def download_resume(lead_id: int, db: Session = Depends(get_db)) -> StreamingResponse:
    """
    Download a lead's resume.

    Args:
        lead_id: ID of the lead whose resume to download
        db: Database session
        current_user: Current user making the request

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

    # Get the file using filesystem storage
    try:
        storage = get_storage(StorageType.FILESYSTEM)
        file_obj = await storage.get_file(db_lead)
        if not file_obj:
            raise HTTPException(status_code=404, detail="Resume file not found")

        return StreamingResponse(
            file_obj,
            media_type=db_lead.resume_mime_type or "application/octet-stream",
            headers={
                "Content-Disposition": (f"attachment; filename={db_lead.resume_original_filename or 'resume'}"),
                "Content-Length": str(db_lead.resume_size or 0) if db_lead.resume_size else "0",
            },
        )
    except Exception as e:
        logger.error(f"Error retrieving resume: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error retrieving resume file") from e


@router.put(
    "/{lead_id}",
    response_model=Lead,
    summary="Update a lead",
    response_description="The updated lead",
    responses={
        404: {"description": "Lead not found"},
        400: {"description": "Invalid status value"},
    },
    dependencies=[Depends(get_current_user)],
)
def update_lead(
    lead_id: int,
    lead_update: LeadUpdate,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user),
) -> Lead:
    """
    Update a lead's information.

    Args:
        lead_id: ID of the lead to update
        lead_update: Fields to update (all optional)
        db: Database session
        current_user: Current user making the request

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


@router.put(
    "/{lead_id}/reached-out",
    response_model=Lead,
    summary="Mark lead as reached out",
    response_description="The updated lead",
    responses={404: {"description": "Lead not found"}},
    dependencies=[Depends(get_current_user)],
)
def mark_lead_reached_out(
    lead_id: int,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user),
) -> Lead:
    """
    Mark a lead as reached out.

    Args:
        lead_id: ID of the lead to mark as reached out
        db: Database session
        current_user: Current user making the request

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


@router.delete(
    "/{lead_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a lead",
    response_description="No content",
    responses={404: {"description": "Lead not found"}},
    dependencies=[Depends(get_current_user)],
)
def delete_lead(
    lead_id: int,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user),
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
    db_lead = db.query(LeadDB).filter(LeadDB.id == lead_id).first()
    if not db_lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    db.delete(db_lead)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
