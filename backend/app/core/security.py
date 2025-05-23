"""Security utilities for password hashing and JWT token handling."""
from datetime import datetime, timedelta
from typing import Any, Optional, Union

from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import ValidationError

from app.core.config import settings
from app.schemas.token import TokenData

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash.

    Args:
        plain_password: The plain text password to verify.
        hashed_password: The hashed password to verify against.

    Returns:
        bool: True if the password matches the hash, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate a password hash.

    Args:
        password: The plain text password to hash.

    Returns:
        str: The hashed password.
    """
    return pwd_context.hash(password)


def create_access_token(
    subject: Union[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """Create a JWT access token.

    Args:
        subject: The subject of the token (usually a user ID or email).
        expires_delta: Optional timedelta for token expiration.

    Returns:
        str: The encoded JWT token.
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def verify_token(token: str) -> Optional[TokenData]:
    """Verify a JWT token and return the token data if valid.

    Args:
        token: The JWT token to verify.

    Returns:
        Optional[TokenData]: The token data if valid, None otherwise.
    """
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        email = payload.get("sub")
        if not email or not isinstance(email, str):
            return None
        return TokenData(email=email)
    except (JWTError, ValidationError):
        return None
