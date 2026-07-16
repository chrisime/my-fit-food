from fastapi import APIRouter, Depends

from app.core.deps import SessionUser, get_session, get_session_admin
from app.core.exceptions import AppException, ErrorCode
from app.models.stock import StockMovement
from app.schemas.stock import BatchExpiresAtUpdate, StockMovementOut
from app.services.stock import compute_stock_balance

router = APIRouter(prefix="/stock", tags=["stock"])


@router.get("/", response_model=list[StockMovementOut])
def list_movements(s: SessionUser = Depends(get_session)):
    return (
        s.db.query(StockMovement)
        .order_by(StockMovement.created_at.desc())
        .limit(200)
        .all()
    )


@router.get("/balance", response_model=list[dict])
def stock_balance(s: SessionUser = Depends(get_session)):
    return compute_stock_balance(s.db)


@router.patch("/batch/expires-at", status_code=204)
def update_batch_expires_at(
    body: BatchExpiresAtUpdate,
    s: SessionUser = Depends(get_session_admin),
):
    movements = (
        s.db.query(StockMovement)
        .filter(
            StockMovement.id.in_(body.movement_ids),
            StockMovement.type == "in",
            StockMovement.reversed.is_(False),
        )
        .all()
    )
    if not movements:
        raise AppException(404, ErrorCode.NOT_FOUND, "No movements found")
    for m in movements:
        m.expires_at = body.expires_at
    s.db.commit()
