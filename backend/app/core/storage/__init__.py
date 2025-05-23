"""Storage abstraction layer for handling file storage across different backends."""

import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, BinaryIO, Dict, Optional

from app.db.models import LeadDB
from app.db.models import StorageType as StorageType


class StorageBackend(ABC):
    """Abstract base class for storage backends."""

    @abstractmethod
    async def save_file(
        self,
        file_data: BinaryIO,
        lead: LeadDB,
        original_filename: str,
        mime_type: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Save a file and return the storage path or identifier."""
        pass

    @abstractmethod
    async def get_file(self, lead: LeadDB) -> Optional[BinaryIO]:
        """Retrieve a file as a file-like object."""
        pass

    @abstractmethod
    async def delete_file(self, lead: LeadDB) -> bool:
        """Delete a file and return True if successful."""
        pass

    @abstractmethod
    def get_file_url(self, lead: LeadDB) -> Optional[str]:
        """Get a URL to access the file if applicable."""
        pass


class FileSystemStorage(StorageBackend):
    """File system storage backend."""

    def __init__(self, base_path: str = "uploads/resumes") -> None:
        """Initialize the filesystem storage backend.

        Args:
            base_path: The base directory path for storing files.
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    async def save_file(
        self,
        file_data: BinaryIO,
        lead: LeadDB,
        original_filename: str,
        mime_type: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Save a file to the filesystem."""
        # Generate a unique filename
        file_extension = Path(original_filename).suffix.lower() or ".bin"
        filename = lead.generate_resume_path(file_extension.lstrip("."))
        filepath = self.base_path / filename

        # Save the file
        with open(filepath, "wb") as f:
            file_data.seek(0)
            f.write(file_data.read())

        # Update lead with file info
        lead.resume_path = str(filepath.relative_to(self.base_path))
        lead.resume_original_filename = original_filename
        lead.resume_mime_type = mime_type
        lead.resume_size = filepath.stat().st_size
        lead.resume_metadata = metadata or {}

        return str(lead.resume_path)

    async def get_file(self, lead: LeadDB) -> Optional[BinaryIO]:
        """Retrieve a file from the filesystem."""
        if not lead.resume_path:
            return None

        filepath = self.base_path / lead.resume_path
        if not filepath.exists():
            return None

        return open(filepath, "rb")

    async def delete_file(self, lead: LeadDB) -> bool:
        """Delete a file from the filesystem."""
        if not lead.resume_path:
            return False

        filepath = self.base_path / lead.resume_path
        if filepath.exists():
            os.unlink(filepath)
            return True
        return False

    def get_file_url(self, lead: LeadDB) -> Optional[str]:
        """Get a URL to access the file."""
        if not lead.resume_path:
            return None
        return f"/api/resumes/{lead.id}/download"


class PostgresStorage(StorageBackend):
    """PostgreSQL storage backend for storing files in the database."""

    def __init__(self) -> None:
        """Initialize the PostgreSQL storage backend."""
        from app.db.base import SessionLocal

        self.SessionLocal = SessionLocal

    async def save_file(
        self,
        file_data: BinaryIO,
        lead: LeadDB,
        original_filename: str,
        mime_type: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Save a file to PostgreSQL."""
        file_data.seek(0)
        file_bytes = file_data.read()

        # In a real implementation, you would store the file bytes in a separate table
        # For now, we'll just store the metadata and use the path as a reference
        file_id = lead.generate_resume_path("")

        # Update lead with file info
        lead.resume_path = file_id
        lead.resume_original_filename = original_filename
        lead.resume_mime_type = mime_type
        lead.resume_size = len(file_bytes)
        lead.resume_metadata = {"stored_in_db": True, **(metadata or {})}

        # Get a new session
        db = self.SessionLocal()
        try:
            # Add the lead to the session and commit
            db.add(lead)
            db.commit()
            db.refresh(lead)
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

        return file_id

    async def get_file(self, lead: LeadDB) -> Optional[BinaryIO]:
        """Retrieve a file from PostgreSQL."""
        if not lead.resume_path:
            return None

        # TODO: Retrieve file bytes from the database
        # For now, return None as we're not actually storing the file content
        return None

    async def delete_file(self, lead: LeadDB) -> bool:
        """Delete a file from PostgreSQL."""
        if not lead.resume_path:
            return False

        # Get a new session
        db = self.SessionLocal()
        try:
            # Clear the file metadata
            lead.resume_path = None
            lead.resume_original_filename = None
            lead.resume_mime_type = None
            lead.resume_size = None
            lead.resume_metadata = None

            # Save the changes
            db.add(lead)
            db.commit()
            return True
        except Exception:
            db.rollback()
            return False
        finally:
            db.close()

    def get_file_url(self, lead: LeadDB) -> Optional[str]:
        """Get a URL to access the file."""
        if not lead.resume_path:
            return None
        return f"/api/resumes/{lead.id}/download"


def get_storage(backend: StorageType = StorageType.FILESYSTEM) -> StorageBackend:
    """
    Factory function to get the appropriate storage backend.

    Args:
        backend: The storage backend type to use.

    Returns:
        An instance of the requested storage backend.

    Raises:
        ValueError: If the specified backend is not supported.
    """
    if backend == StorageType.FILESYSTEM:
        return FileSystemStorage()
    elif backend == StorageType.POSTGRES:
        return PostgresStorage()
    else:
        raise ValueError(f"Unsupported storage backend: {backend}")
