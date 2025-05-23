import logging
import sys
from datetime import datetime
from io import BytesIO
from typing import Any, BinaryIO, Dict, Optional, Tuple, Union

# Third-party imports
import magic  # type: ignore[import-untyped]  # No type stubs available
from fastapi import HTTPException, UploadFile

# Ignore type checking for magic module
# mypy: ignore-errors

# Set up logging
logger = logging.getLogger(__name__)

# Type aliases for better readability
FileLike = Union[BinaryIO, BytesIO, UploadFile]  # type: ignore[valid-type]  # Allowed types for file operations


class FileUploadManager:
    """Manages file uploads with validation and storage."""

    def __init__(
        self,
        allowed_types: Optional[Dict[str, str]] = None,
        max_size: int = 5 * 1024 * 1024,
    ):
        """Initialize the file upload manager.

        Args:
            allowed_types: Dictionary mapping MIME types to file extensions
            max_size: Maximum file size in bytes (default: 5MB)
        """
        self.allowed_types = allowed_types or {
            "application/pdf": "pdf",
            "image/jpeg": "jpg",
            "image/png": "png",
        }
        self.max_size = max_size

    @staticmethod
    def get_mime_type(buffer: bytes) -> str:
        """Get the MIME type of a file buffer.

        Args:
            buffer: The file content as bytes

        Returns:
            str: The detected MIME type, or 'application/octet-stream' if
                detection fails
        """
        try:
            if sys.platform == "win32":
                # On Windows, we need to use the Magic class
                mime = magic.Magic(mime=True)
                result = mime.from_buffer(buffer)
                return str(result)  # Ensure we return a string
            else:
                # On Unix-like systems, we can use the module-level function
                result = magic.from_buffer(buffer, mime=True)
                return str(result)  # Ensure we return a string
        except Exception as e:
            logger.warning("Failed to detect MIME type: %s", str(e))
            return "application/octet-stream"

    def get_file_extension(self, file: UploadFile) -> str:
        """Get the file extension from the MIME type."""
        file_content = file.file.read(1024)
        file.file.seek(0)  # Reset file pointer
        mime_type = self.get_mime_type(file_content)
        return self.allowed_types.get(mime_type, "")

    async def validate_file(self, file: UploadFile) -> Tuple[bool, str, Dict[str, Any]]:
        """Validate the uploaded file.

        Args:
            file: The uploaded file

        Returns:
            Tuple of (is_valid, error_message, file_metadata)
        """
        metadata: Dict[str, Any] = {}

        # Check if file is empty
        if not file.filename:
            return False, "No file selected", metadata

        # Get file size
        file_size = 0
        file_content = b""

        # Read file in chunks to get size and content
        while True:
            chunk = await file.read(8192)
            if not chunk:
                break
            file_size += len(chunk)
            file_content += chunk

            # Check file size limit
            if file_size > self.max_size:
                return (
                    False,
                    f"File size exceeds the maximum allowed size of {self.max_size / (1024 * 1024):.1f}MB",
                    metadata,
                )

        # Reset file pointer
        file.file = BytesIO(file_content)

        # Get file extension
        file_extension = self.get_file_extension(file)
        if not file_extension:
            allowed_types = ", ".join(self.allowed_types.values())
            return (
                False,
                f"Unsupported file type. Allowed types: {allowed_types}",
                metadata,
            )

        # Get MIME type
        mime_type = self.get_mime_type(file_content[:1024])

        # Prepare metadata
        metadata.update(
            {
                "original_filename": file.filename,
                "content_type": mime_type,
                "size": file_size,
                "extension": file_extension,
            }
        )

        return True, "", metadata

    async def save_file(
        self,
        file: UploadFile,
        lead_id: int,
        storage_config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Save an uploaded file using the filesystem storage backend.

        Args:
            file: The uploaded file
            lead_id: ID of the lead this file belongs to
            storage_config: Additional configuration for the storage backend

        Returns:
            Dictionary containing file metadata and storage information

        Raises:
            HTTPException: If there's an error saving the file
        """
        from app.core.storage import StorageType, get_storage
        from app.db.base import SessionLocal
        from app.db.models import LeadDB

        db = SessionLocal()
        try:
            # Get the lead
            lead = db.query(LeadDB).filter(LeadDB.id == lead_id).first()
            if not lead:
                raise HTTPException(status_code=404, detail="Lead not found")

            # Validate the file
            is_valid, error_msg, file_metadata = await self.validate_file(file)
            if not is_valid:
                raise HTTPException(status_code=400, detail=error_msg)

            # Use filesystem storage
            storage = get_storage(StorageType.FILESYSTEM)

            # Save the file using the storage backend
            await storage.save_file(
                file_data=file.file,
                lead=lead,
                original_filename=file_metadata["original_filename"],
                mime_type=file_metadata["content_type"],
                metadata={
                    "uploaded_at": datetime.utcnow().isoformat(),
                    **(storage_config or {}),
                },
            )

            # Update the lead in the database
            db.add(lead)
            db.commit()

            # Prepare minimal response
            result = {"success": True, "download_url": storage.get_file_url(lead)}

            logger.info(
                "File saved successfully",
                extra={
                    "action": "save_file",
                    "lead_id": lead_id,
                    "file_size": file_metadata["size"],
                },
            )

            return result

        except HTTPException:
            db.rollback()
            raise

        except Exception as e:
            db.rollback()
            logger.error(
                f"Error saving file: {str(e)}",
                exc_info=True,
                extra={
                    "action": "save_file",
                    "lead_id": lead_id,
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
            )
            raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")

        finally:
            db.close()


# Create a default instance
default_file_uploader = FileUploadManager()
