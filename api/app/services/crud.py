from collections.abc import Callable

from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.exceptions import AppException, ErrorCode


def get_or_404(db: Session, model, id: int, detail: str = "Not found"):
    obj = db.query(model).filter(model.id == id).first()
    if not obj:
        raise AppException(status_code=404, code=ErrorCode.NOT_FOUND, detail=detail)
    return obj


def create_from_schema(db: Session, model, schema: BaseModel) -> object:
    obj = model(**schema.model_dump())
    db.add(obj)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(obj)
    return obj


def update_from_schema(db: Session, model, id: int, schema: BaseModel, detail: str = "Not found"):
    obj = get_or_404(db, model, id, detail)
    for key, val in schema.model_dump(exclude_unset=True).items():
        setattr(obj, key, val)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(obj)
    return obj
