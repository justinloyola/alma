# Standard library imports
from datetime import datetime
from enum import Enum
from typing import Optional

# Third-party imports
from pydantic import BaseModel, EmailStr, Field, validator


class LeadStatus(str, Enum):
    PENDING = "pending"
    REACHED_OUT = "reached_out"


class LeadBase(BaseModel):
    """Base schema for Lead with common fields."""

    first_name: str = Field(
        ..., min_length=1, max_length=100, description="Lead's first name"
    )
    last_name: str = Field(
        ..., min_length=1, max_length=100, description="Lead's last name"
    )
    email: EmailStr = Field(..., description="Lead's email address")
    status: LeadStatus = Field(
        default=LeadStatus.PENDING, description="Current status of the lead"
    )

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

    pass


class LeadUpdate(BaseModel):
    """Schema for updating a lead. All fields are optional."""

    first_name: Optional[str] = Field(
        None, min_length=1, max_length=100, description="Lead's first name"
    )
    last_name: Optional[str] = Field(
        None, min_length=1, max_length=100, description="Lead's last name"
    )
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
    created_at: datetime = Field(..., description="Timestamp when the lead was created")
    updated_at: datetime = Field(
        ..., description="Timestamp when the lead was last updated"
    )

    # Internal fields that should not be exposed in the API
    resume_path: Optional[str] = Field(None, exclude=True)
    resume_original_filename: Optional[str] = Field(None, exclude=True)
    resume_mime_type: Optional[str] = Field(None, exclude=True)
    resume_size: Optional[int] = Field(None, exclude=True)
    resume_storage_type: Optional[str] = Field(None, exclude=True)

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
