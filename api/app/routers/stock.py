from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.models.product import Product
from app.models.stock import StockMovement
from app.models.user import User
from app.schemas.stock import StockAdjust, StockMovementOut

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
    product = db.query(Product).filter(Product.id == body.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
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
    products = db.query(Product).filter(Product.is_active.is_(True)).all()
    result = []
    for p in products:
        total_in = (
            db.query(StockMovement)
            .filter(
                StockMovement.product_id == p.id,
                StockMovement.type == "in",
            )
            .with_entities(StockMovement.quantity)
            .all()
        )
        total_out = (
            db.query(StockMovement)
            .filter(
                StockMovement.product_id == p.id,
                StockMovement.type == "out",
            )
            .with_entities(StockMovement.quantity)
            .all()
        )
        balance = sum(q[0] for q in total_in) - sum(q[0] for q in total_out)
        result.append(
            {
                "product_id": p.id,
                "product_name": p.name,
                "unit": p.unit,
                "balance": balance,
            }
        )
    return result
