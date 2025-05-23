"""Pydantic models for token related schemas."""
from pydantic import BaseModel, EmailStr


class Token(BaseModel):
    """JWT token response model."""

    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token payload data model."""

    email: EmailStr | None = None
    scopes: list[str] = []
