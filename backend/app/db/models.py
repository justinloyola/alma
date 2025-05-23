import enum
import uuid
from datetime import datetime
from typing import Any, Dict

from sqlalchemy import JSON, Column, DateTime, Enum, Integer, String

from .base import Base


class StorageType(str, enum.Enum):
    FILESYSTEM = "filesystem"
    POSTGRES = "postgres"


class LeadStatus(str, enum.Enum):
    PENDING = "pending"
    REACHED_OUT = "reached_out"


class LeadDB(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)

    # Resume storage fields
    resume_storage_type = Column(
        Enum(StorageType), default=StorageType.FILESYSTEM, nullable=False
    )
    resume_path = Column(
        String(512), nullable=True
    )  # Path or identifier based on storage type
    resume_original_filename = Column(String(255), nullable=True)
    resume_mime_type = Column(String(100), nullable=True)
    resume_size = Column(Integer, nullable=True)  # Size in bytes
    resume_metadata = Column(JSON, nullable=True)  # Additional metadata as JSON

    status = Column(Enum(LeadStatus), default=LeadStatus.PENDING, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    @property
    def resume_info(self) -> Dict[str, Any]:
        """Get resume information in a structured format."""
        return {
            "storage_type": self.resume_storage_type.value,
            "path": self.resume_path,
            "original_filename": self.resume_original_filename,
            "mime_type": self.resume_mime_type,
            "size": self.resume_size,
            "metadata": self.resume_metadata or {},
        }

    def generate_resume_path(self, file_extension: str) -> str:
        """Generate a unique path for storing the resume using UUID.

        Args:
            file_extension: The file extension to use (e.g., 'pdf', 'docx')

        Returns:
            A unique string identifier for the resume file
        """
        # Always use UUID for consistent behavior across storage types
        unique_id = str(uuid.uuid4())
        if file_extension:
            return f"{unique_id}.{file_extension}"
        return unique_id

    def __repr__(self):
        return f"<Lead {self.first_name} {self.last_name} ({self.email})>"
