from typing import Optional

from pydantic import BaseModel, EmailStr, Field, validator


class Token(BaseModel):
    """Schema for access token response."""

    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Schema for token data."""

    email: Optional[str] = None


class UserBase(BaseModel):
    """Base schema for user data."""

    email: EmailStr
    is_active: bool = True
    is_superuser: bool = False


class UserCreate(UserBase):
    """Schema for user creation."""

    password: str = Field(..., min_length=8, max_length=100)

    @validator("password")
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        # Add more password strength validations as needed
        return v


class UserUpdate(BaseModel):
    """Schema for user updates."""

    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=8, max_length=100)
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None


class UserInDB(UserBase):
    """Schema for user data in database."""

    id: int
    hashed_password: str

    class Config:
        orm_mode = True


class User(UserBase):
    """Schema for user response."""

    id: int

    class Config:
        orm_mode = True
