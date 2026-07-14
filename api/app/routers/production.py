from fastapi import APIRouter, Depends, HTTPException, WebSocket
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.production import Production as ProductionModel
from app.models.stock import StockMovement
from app.models.product import Product
from app.models.user import User
from app.schemas.stock import ProductionCreate, ProductionOut
from app.ws.manager import notify_clients

router = APIRouter(prefix="/production", tags=["production"])


@router.post("/", response_model=ProductionOut, status_code=201)
def create_production(
    body: ProductionCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    product = db.query(Product).filter(Product.id == body.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    prod = ProductionModel(
        product_id=body.product_id,
        quantity=body.quantity,
        notes=body.notes,
        created_by=user.id,
    )
    db.add(prod)

    movement = StockMovement(
        product_id=body.product_id,
        type="in",
        quantity=body.quantity,
        reference_type="production",
        reference_id=prod.id,
        notes=body.notes,
        created_by=user.id,
    )
    db.add(movement)
    db.commit()
    db.refresh(prod)

    notify_clients("stock_updated", {"product_id": body.product_id})

    return prod
