from datetime import timedelta
from typing import Any, Optional

from fastapi import APIRouter, Depends, Form, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app import crud
from app.api import deps
from app.core import security
from app.core.config import settings
from app.db.deps import get_db
from app.db.models import UserDB
from app.models.user import Token, User

router = APIRouter()


class OAuth2PasswordRequestFormExtended(OAuth2PasswordRequestForm):
    """Extended OAuth2 password request form with optional grant_type."""

    def __init__(
        self,
        *,
        username: str = Form(...),
        password: str = Form(...),
        grant_type: str = Form("password", regex="^password$"),
        scope: str = Form(""),
        client_id: Optional[str] = Form(None),
        client_secret: Optional[str] = Form(None),
    ):
        super().__init__(
            grant_type=grant_type,
            username=username,
            password=password,
            scope=scope,
            client_id=client_id,
            client_secret=client_secret,
        )


@router.post("/login/access-token", response_model=Token)
async def login_access_token(
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestFormExtended = Depends(),
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    user = crud.user.authenticate(db, email=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password",
        )
    elif not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": security.create_access_token(user.email, expires_delta=access_token_expires),
        "token_type": "bearer",
    }


@router.post("/login/test-token", response_model=User)
def test_token(current_user: UserDB = Depends(deps.get_current_user)) -> Any:
    """
    Test access token
    """
    return current_user
