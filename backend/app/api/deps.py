from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app import crud
from app.core.config import settings
from app.core.security import verify_token
from app.db.deps import get_db
from app.db.models import UserDB

reusable_oauth2 = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")


def get_current_user(db: Session = Depends(get_db), token: str = Depends(reusable_oauth2)) -> UserDB:
    """Get the current user from the token."""
    print(f"Verifying token: {token}")
    token_data = verify_token(token)
    print(f"Token data: {token_data}")

    if not token_data or not token_data.email:
        print("Invalid token data or missing email")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # At this point, token_data.email is guaranteed to be a string
    print(f"Looking for user with email: {token_data.email}")
    user = crud.user.get_by_email(db, email=token_data.email)
    print(f"Found user: {user}")

    if not user:
        # List all users in the database for debugging
        all_users = db.query(UserDB).all()
        print(f"All users in database: {[u.email for u in all_users]}")

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    print(f"Returning user: {user.email}")
    return user


def get_current_active_user(
    current_user: UserDB = Depends(get_current_user),
) -> UserDB:
    """Check if the current user is active."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )
    return current_user


def get_current_active_superuser(
    current_user: UserDB = Depends(get_current_user),
) -> UserDB:
    """Check if the current user is a superuser."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges",
        )
    return current_user
