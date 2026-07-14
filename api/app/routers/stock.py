from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.models.product import Product
from app.models.stock import StockMovement
from app.models.user import User
from app.schemas.stock import StockAdjust, StockMovementOut
from app.services.crud import get_or_404
from app.services.stock import compute_stock_balance

router = APIRouter(prefix="/stock", tags=["stock"])


@router.get("/", response_model=list[StockMovementOut])
def list_movements(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return (
        db.query(StockMovement)
        .order_by(StockMovement.created_at.desc())
        .limit(200)
        .all()
    )


@router.post("/adjust", response_model=StockMovementOut, status_code=201)
def adjust_stock(
    body: StockAdjust,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("admin")),
):
    get_or_404(db, Product, body.product_id, "Product not found")
    movement = StockMovement(
        product_id=body.product_id,
        type=body.type,
        quantity=body.quantity,
        notes=body.notes or f"Ajuste manual ({body.type})",
        created_by=user.id,
    )
    db.add(movement)
    db.commit()
    db.refresh(movement)
    return movement


@router.get("/balance", response_model=list[dict])
def stock_balance(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return compute_stock_balance(db)
