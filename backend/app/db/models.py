import enum
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from passlib.context import CryptContext
from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.storage import StorageType

from .base import BaseModelWithId

__all__ = ["LeadDB", "UserDB", "LeadStatus"]

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class LeadStatus(str, enum.Enum):
    """Enum for lead statuses."""

    PENDING = "pending"
    REACHED_OUT = "reached_out"


class UserDB(BaseModelWithId):
    """User database model."""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships (none needed for now)

    def set_password(self, password: str) -> None:
        """Hash and set the user's password."""
        self.hashed_password = pwd_context.hash(password)

    def verify_password(self, password: str) -> bool:
        """Verify a password against the stored hash."""
        return pwd_context.verify(password, self.hashed_password)

    def __repr__(self) -> str:
        return f"<UserDB(id={self.id}, email={self.email})>"


class LeadDB(BaseModelWithId):
    """Lead database model."""

    __tablename__ = "leads"
    __table_args__ = (
        CheckConstraint(
            "resume_storage_type IN ('filesystem', 'postgres')",
            name="ck_leads_resume_storage_type",
        ),
        CheckConstraint("status IN ('pending', 'reached_out')", name="ck_leads_status"),
    )

    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )

    # Resume information - using String instead of Enum for SQLite compatibility
    resume_storage_type: Mapped[str] = mapped_column(
        String(20), default=StorageType.FILESYSTEM.value, nullable=False
    )
    resume_path: Mapped[Optional[str]] = mapped_column(
        String(36),  # UUIDs are 36 characters long
        nullable=True,
        unique=True,
        index=True,
    )
    resume_original_filename: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    resume_mime_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    resume_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    resume_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True
    )

    # Status
    status: Mapped[str] = mapped_column(
        String(20), default=LeadStatus.PENDING.value, nullable=False
    )

    @property
    def resume_info(self) -> Dict[str, Any]:
        """
        Get resume information in a structured format.

        Returns:
            Dict[str, Any]: A dictionary containing resume information.
        """
        # Convert storage type to string if it's an enum
        storage_type = self.resume_storage_type
        if hasattr(storage_type, "value"):
            storage_type = storage_type.value

        return {
            "storage_type": storage_type,
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
