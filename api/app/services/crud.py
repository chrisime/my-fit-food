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
    db.commit()
    db.refresh(obj)
    return obj


def update_from_schema(db: Session, model, id: int, schema: BaseModel, detail: str = "Not found"):
    obj = get_or_404(db, model, id, detail)
    for key, val in schema.model_dump(exclude_unset=True).items():
        setattr(obj, key, val)
    db.commit()
    db.refresh(obj)
    return obj


def delete_object(
    db: Session,
    model,
    id: int,
    detail: str = "Not found",
    before_delete: Callable[[object], None] | None = None,
    on_fk_error: Callable[[Exception], None] | None = None,
) -> None:
    obj = get_or_404(db, model, id, detail)
    if before_delete:
        before_delete(obj)
    db.delete(obj)
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        if on_fk_error:
            on_fk_error(e)
        else:
            raise
