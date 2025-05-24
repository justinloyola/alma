"""Application configuration settings."""

import os
from typing import List, Optional, Union

from pydantic import ValidationInfo, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    # Application settings
    PROJECT_NAME: str = "Alma Lead Management"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"

    # Security
    SECRET_KEY: str = "your-secret-key-here"  # Change this in production
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    @field_validator("CORS_ORIGINS")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str], None]) -> List[str]:
        """Parse CORS origins from string or list."""
        if v is None:
            return []

        if isinstance(v, str):
            if not v:
                return []
            if v.startswith("[") and v.endswith("]"):
                # Handle JSON array string
                import json

                try:
                    parsed = json.loads(v)
                    if isinstance(parsed, list):
                        return [str(item) for item in parsed]
                    return [str(parsed)]
                except json.JSONDecodeError:
                    pass
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return [str(item) for item in v]

        raise ValueError(f"Invalid CORS origins value: {v}")

    # Database
    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "sqlite")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "")
    SQLALCHEMY_DATABASE_URI: Optional[str] = os.getenv("DATABASE_URL", "sqlite:///./alma.db")

    @field_validator("SQLALCHEMY_DATABASE_URI", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: Optional[str], info: ValidationInfo) -> str:
        """Assemble the database connection string."""
        # If a database URL is provided, use it
        if v and isinstance(v, str):
            return v

        # Get database configuration from environment or defaults
        data = info.data or {}

        # For SQLite
        if data.get("POSTGRES_SERVER") == "sqlite":
            return "sqlite:///./alma.db"

        # For PostgreSQL - ensure all values are strings and not None
        user = str(data.get("POSTGRES_USER", "") or "")
        password = str(data.get("POSTGRES_PASSWORD", "") or "")
        server = str(data.get("POSTGRES_SERVER", "localhost") or "localhost")
        db_name = str(data.get("POSTGRES_DB", "alma") or "alma")

        # Construct the connection string
        if user and password:
            return f"postgresql://{user}:{password}@{server}/{db_name}"
        return f"postgresql://{server}/{db_name}"

    # File uploads
    MAX_FILE_SIZE: int = 5 * 1024 * 1024  # 5MB in bytes
    UPLOAD_DIR: str = "uploads/resumes"

    # Model configuration
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="ignore")


# Create settings instance
settings = Settings()
