from typing import NamedTuple

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import AppException, ErrorCode
from app.core.security import decode_access_token
from app.models.user import User

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise AppException(
            401, ErrorCode.TOKEN_EXPIRED, "Invalid token",
        )
    user = db.query(User).filter(User.id == int(payload.get("sub"))).first()
    if not user:
        raise AppException(
            401, ErrorCode.INVALID_CREDENTIALS, "User not found",
        )
    return user


def require_role(role: str):
    def checker(user: User = Depends(get_current_user)) -> User:
        if user.role != role and user.role != "admin":
            raise AppException(
                403, ErrorCode.FORBIDDEN, f"Role '{role}' required",
            )
        return user
    return checker


class SessionUser(NamedTuple):
    db: Session
    user: User


def get_session(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> SessionUser:
    return SessionUser(db=db, user=user)


def get_session_admin(
    db: Session = Depends(get_db),
    user: User = Depends(require_role("admin")),
) -> SessionUser:
    return SessionUser(db=db, user=user)
