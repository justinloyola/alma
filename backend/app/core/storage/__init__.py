"""Storage abstraction layer for handling file storage across different backends."""

from abc import ABC, abstractmethod
from enum import Enum
from io import BytesIO
from pathlib import Path
from typing import TYPE_CHECKING, Any, BinaryIO, Dict, Optional

if TYPE_CHECKING:
    from app.db.models import LeadDB


class StorageType(str, Enum):
    """Enum for storage types."""

    FILESYSTEM = "filesystem"
    POSTGRES = "postgres"


class StorageBackend(ABC):
    """Abstract base class for storage backends."""

    @abstractmethod
    async def save_file(
        self,
        file_data: BinaryIO,
        lead: "LeadDB",
        original_filename: str,
        mime_type: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Save a file and return the storage path or identifier."""
        pass

    @abstractmethod
    async def get_file(self, lead: "LeadDB") -> Optional[BinaryIO]:
        """Retrieve a file as a file-like object."""
        pass

    @abstractmethod
    async def delete_file(self, lead: "LeadDB") -> bool:
        """Delete a file and return True if successful."""
        pass

    @abstractmethod
    def get_file_url(self, lead: "LeadDB") -> Optional[str]:
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
        lead: "LeadDB",
        original_filename: str,
        mime_type: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Save a file to the filesystem."""
        # Generate a unique filename with UUID
        import uuid

        file_ext = Path(original_filename).suffix.lower()
        filename = f"{uuid.uuid4()}{file_ext}"
        file_path = self.base_path / filename

        # Save the file
        with open(file_path, "wb") as f:
            f.write(file_data.read())

        return str(file_path.relative_to(self.base_path))

    async def get_file(self, lead: "LeadDB") -> Optional[BinaryIO]:
        """Retrieve a file from the filesystem."""
        if not lead.resume_path:
            return None

        file_path = self.base_path / lead.resume_path
        if not file_path.exists():
            return None

        return open(file_path, "rb")

    async def delete_file(self, lead: "LeadDB") -> bool:
        """Delete a file from the filesystem."""
        if not lead.resume_path:
            return False

        file_path = self.base_path / lead.resume_path
        if file_path.exists():
            file_path.unlink()
            return True
        return False

    def get_file_url(self, lead: "LeadDB") -> Optional[str]:
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
        lead: "LeadDB",
        original_filename: str,
        mime_type: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Save a file to PostgreSQL."""
        from app.db.models import LeadDB as DBLead

        db = self.SessionLocal()
        try:
            db_lead = db.query(DBLead).filter(DBLead.id == lead.id).first()
            if not db_lead:
                raise ValueError(f"Lead with id {lead.id} not found")

            file_content = file_data.read()
            db_lead.resume_data = file_content
            db_lead.resume_mime_type = mime_type
            db_lead.resume_original_filename = original_filename
            db_lead.resume_size = len(file_content)

            db.commit()
            return f"postgres://{lead.id}"
        finally:
            db.close()

    async def get_file(self, lead: "LeadDB") -> Optional[BinaryIO]:
        """Retrieve a file from PostgreSQL."""
        from app.db.models import LeadDB as DBLead

        db = self.SessionLocal()
        try:
            db_lead = db.query(DBLead).filter(DBLead.id == lead.id).first()
            if not db_lead or not db_lead.resume_data:
                return None

            return BytesIO(db_lead.resume_data)
        finally:
            db.close()

    async def delete_file(self, lead: "LeadDB") -> bool:
        """Delete a file from PostgreSQL."""
        from app.db.models import LeadDB as DBLead

        db = self.SessionLocal()
        try:
            db_lead = db.query(DBLead).filter(DBLead.id == lead.id).first()
            if not db_lead or not db_lead.resume_data:
                return False

            db_lead.resume_data = None
            db_lead.resume_mime_type = None
            db_lead.resume_original_filename = None
            db_lead.resume_size = None

            db.commit()
            return True
        finally:
            db.close()

    def get_file_url(self, lead: "LeadDB") -> Optional[str]:
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


__all__ = [
    "StorageType",
    "StorageBackend",
    "FileSystemStorage",
    "PostgresStorage",
    "get_storage",
]
