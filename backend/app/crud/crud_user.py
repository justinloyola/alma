from typing import Any, Dict, Optional, Union

from sqlalchemy.orm import Session

from app.core.security import get_password_hash, verify_password
from app.crud.base import CRUDBase
from app.db.models import UserDB
from app.models.user import UserCreate, UserUpdate


class CRUDUser(CRUDBase[UserDB, UserCreate, UserUpdate]):
    def get_by_email(self, db: Session, *, email: str) -> Optional[UserDB]:
        return db.query(UserDB).filter(UserDB.email == email).first()

    def create(self, db: Session, *, obj_in: UserCreate) -> UserDB:
        db_obj = UserDB(
            email=obj_in.email,
            hashed_password=get_password_hash(obj_in.password),
            is_superuser=obj_in.is_superuser,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self, db: Session, *, db_obj: UserDB, obj_in: Union[UserUpdate, Dict[str, Any]]
    ) -> UserDB:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)

        if "password" in update_data and update_data["password"]:
            hashed_password = get_password_hash(update_data["password"])
            del update_data["password"]
            update_data["hashed_password"] = hashed_password

        return super().update(db, db_obj=db_obj, obj_in=update_data)

    def authenticate(
        self, db: Session, *, email: str, password: str
    ) -> Optional[UserDB]:
        user = self.get_by_email(db, email=email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    def is_active(self, user: UserDB) -> bool:
        return user.is_active

    def is_superuser(self, user: UserDB) -> bool:
        return user.is_superuser


user = CRUDUser(UserDB)
