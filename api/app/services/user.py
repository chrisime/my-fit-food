from sqlalchemy.orm import Session

from app.core.exceptions import AppException, ErrorCode
from app.core.security import hash_password
from app.models.user import User
from app.schemas.user import UserCreate


def list_users(db: Session) -> list[User]:
    return db.query(User).order_by(User.full_name).all()


def create_user(db: Session, body: UserCreate) -> User:
    existing = db.query(User).filter(User.username == body.username).first()
    if existing:
        raise AppException(400, ErrorCode.USERNAME_DUPLICATE, "Username already taken")
    user = User(
        username=body.username,
        hashed_password=hash_password(body.password),
        full_name=body.full_name,
        role=body.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_user(db: Session, user_id: int, body: UserCreate) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise AppException(404, ErrorCode.USER_NOT_FOUND, "User not found")
    user.username = body.username
    user.full_name = body.full_name
    user.role = body.role
    if body.password:
        user.hashed_password = hash_password(body.password)
    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user_id: int, current_user_id: int) -> None:
    if current_user_id == user_id:
        raise AppException(400, ErrorCode.USER_SELF_DELETE, "Cannot delete yourself")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise AppException(404, ErrorCode.USER_NOT_FOUND, "User not found")
    db.delete(user)
    db.commit()
