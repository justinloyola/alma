# Standard library imports
from datetime import datetime
from enum import Enum
from typing import Any, Optional

# Third-party imports
from pydantic import BaseModel, EmailStr, Field, validator


class LeadStatus(str, Enum):
    PENDING = "pending"
    REACHED_OUT = "reached_out"


class LeadBase(BaseModel):
    """Base schema for Lead with common fields."""

    first_name: str = Field(..., min_length=1, max_length=100, description="Lead's first name")
    last_name: str = Field(..., min_length=1, max_length=100, description="Lead's last name")
    email: EmailStr = Field(..., description="Lead's email address")
    status: LeadStatus = Field(default=LeadStatus.PENDING, description="Current status of the lead")
    created_at: Optional[datetime] = Field(None, description="Timestamp when the lead was created")
    updated_at: Optional[datetime] = Field(None, description="Timestamp when the lead was last updated")

    class Config:
        json_schema_extra = {
            "example": {
                "first_name": "John",
                "last_name": "Doe",
                "email": "john.doe@example.com",
                "status": "new",
            }
        }


class LeadCreate(LeadBase):
    """Schema for creating a new lead."""

    # Explicitly include these fields with default values to avoid mypy errors
    created_at: Optional[datetime] = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when the lead was created",
    )
    updated_at: Optional[datetime] = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when the lead was last updated",
    )

    # Override status with a default value
    status: LeadStatus = Field(default=LeadStatus.PENDING, description="Current status of the lead")


class LeadUpdate(BaseModel):
    """Schema for updating a lead. All fields are optional."""

    first_name: Optional[str] = Field(None, min_length=1, max_length=100, description="Lead's first name")
    last_name: Optional[str] = Field(None, min_length=1, max_length=100, description="Lead's last name")
    email: Optional[EmailStr] = Field(None, description="Lead's email address")
    status: Optional[LeadStatus] = Field(None, description="Current status of the lead")

    @validator("email")
    def email_must_not_be_empty(cls, v: Optional[EmailStr]) -> Optional[EmailStr]:
        """
        Validate that email is not an empty string if provided.

        Args:
            v: The email value to validate.

        Returns:
            The validated email if not empty.

        Raises:
            ValueError: If the email is an empty string.
        """
        if v == "":
            raise ValueError("Email cannot be empty")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "first_name": "John",
                "last_name": "Doe",
                "email": "john.doe@example.com",
                "status": "contacted",
            }
        }


class Lead(LeadBase):
    """Complete Lead schema including read-only fields."""

    id: int = Field(..., description="Unique identifier for the lead")
    created_at: Optional[datetime] = Field(None, description="Timestamp when the lead was created")
    updated_at: Optional[datetime] = Field(None, description="Timestamp when the lead was last updated")

    # Internal fields that should not be exposed in the API
    resume_path: Optional[str] = Field(None, exclude=True)
    resume_original_filename: Optional[str] = Field(None, exclude=True)
    resume_mime_type: Optional[str] = Field(None, exclude=True)
    resume_size: Optional[int] = Field(None, exclude=True)

    @classmethod
    def from_orm(cls, obj: Any) -> "Lead":
        """Convert ORM model to Pydantic model."""
        if not obj:
            raise ValueError("Cannot create Lead from None")

        # Convert status to enum if it's a string
        status = obj.status
        if isinstance(status, str):
            status = LeadStatus(status)

        return cls(
            id=obj.id,
            first_name=obj.first_name,
            last_name=obj.last_name,
            email=obj.email,
            status=status,
            created_at=obj.created_at,
            updated_at=obj.updated_at,
            resume_path=obj.resume_path,
            resume_original_filename=obj.resume_original_filename,
            resume_mime_type=obj.resume_mime_type,
            resume_size=obj.resume_size,
        )

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "first_name": "John",
                "last_name": "Doe",
                "email": "john.doe@example.com",
                "status": "new",
                "created_at": "2023-01-01T00:00:00",
                "updated_at": "2023-01-01T00:00:00",
            }
        }
