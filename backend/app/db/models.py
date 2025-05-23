import enum
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import JSON, DateTime, Enum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base as BaseModelWithId

__all__ = ["BaseModelWithId", "LeadDB", "StorageType", "LeadStatus"]


class StorageType(str, enum.Enum):
    FILESYSTEM = "filesystem"
    POSTGRES = "postgres"


class LeadStatus(str, enum.Enum):
    PENDING = "pending"
    REACHED_OUT = "reached_out"


class LeadDB(BaseModelWithId):
    __tablename__ = "leads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )

    # Resume storage fields
    resume_storage_type: Mapped[StorageType] = mapped_column(
        Enum(StorageType), default=StorageType.FILESYSTEM, nullable=False
    )
    resume_path: Mapped[Optional[str]] = mapped_column(
        String(512), nullable=True
    )  # Path or identifier based on storage type
    resume_original_filename: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    resume_mime_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    resume_size: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )  # Size in bytes
    resume_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True
    )  # Additional metadata as JSON

    status: Mapped[LeadStatus] = mapped_column(
        Enum(LeadStatus), default=LeadStatus.PENDING, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    @property
    def resume_info(self) -> Dict[str, Any]:
        """
        Get resume information in a structured format.

        Returns:
            Dict[str, Any]: A dictionary containing resume information.
        """
        return {
            "storage_type": self.resume_storage_type.value,
            "path": self.resume_path,
            "original_filename": self.resume_original_filename,
            "mime_type": self.resume_mime_type,
            "size": self.resume_size,
            "metadata": self.resume_metadata,
        }

    def update_status(self, new_status: str) -> None:
        """
        Update the lead status with validation.

        Args:
            new_status: The new status to set for the lead.
                Must be one of the values in LeadStatus.

        Raises:
            ValueError: If the provided status is not valid.
        """
        if new_status not in LeadStatus._value2member_map_:
            raise ValueError(f"Invalid status: {new_status}")
        self.status = LeadStatus(new_status)
        self.updated_at = datetime.utcnow()

    def generate_resume_path(self, file_extension: str) -> str:
        """
        Generate a unique path for storing the resume using UUID.

        Args:
            file_extension: The file extension to use (e.g., 'pdf', 'docx')

        Returns:
            str: A unique string identifier for the resume file
        """
        # Always use UUID for consistent behavior across storage types
        unique_id = str(uuid.uuid4())
        if file_extension:
            return f"{unique_id}.{file_extension}"
        return unique_id

    def __repr__(self) -> str:
        """
        Return a string representation of the LeadDB instance.

        Returns:
            str: A string representation of the lead.
        """
        return f"<Lead {self.first_name} {self.last_name} ({self.email})>"
