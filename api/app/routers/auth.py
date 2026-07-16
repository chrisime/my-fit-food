from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import SessionUser, get_session, get_session_admin
from app.core.exceptions import AppException
from app.core.security import create_access_token, verify_password
from app.models.user import User
from app.schemas.user import LoginRequest, Token, UserCreate, UserOut
from app.services.user import create_user, delete_user, list_users, update_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=Token)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == body.username).first()
    if not user or not verify_password(body.password, user.hashed_password):
        raise AppException(
            401, 1001, "Invalid credentials",
        )
    token = create_access_token({"sub": user.id, "role": user.role})
    return Token(access_token=token, user=UserOut.model_validate(user))


@router.post("/users", response_model=UserOut)
def create_user_endpoint(body: UserCreate, s: SessionUser = Depends(get_session_admin)):
    return create_user(s.db, body)


@router.get("/users", response_model=list[UserOut])
def list_users_endpoint(s: SessionUser = Depends(get_session_admin)):
    return list_users(s.db)


@router.put("/users/{user_id}", response_model=UserOut)
def update_user_endpoint(user_id: int, body: UserCreate, s: SessionUser = Depends(get_session_admin)):
    return update_user(s.db, user_id, body)


@router.delete("/users/{user_id}", status_code=204)
def delete_user_endpoint(user_id: int, s: SessionUser = Depends(get_session_admin)):
    delete_user(s.db, user_id, s.user.id)


@router.get("/users/me", response_model=UserOut)
def me(s: SessionUser = Depends(get_session)):
    return s.user
