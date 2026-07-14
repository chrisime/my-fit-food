from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.order import Order
from app.models.product import Product
from app.models.stock import StockMovement
from app.models.user import User

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/")
def dashboard(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    today_start = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )

    orders_today = (
        db.query(Order)
        .filter(Order.created_at >= today_start)
        .count()
    )

    pending_payments = (
        db.query(Order)
        .filter(
            Order.payment_status == "pending",
            Order.status != "delivered",
        )
        .count()
    )

    delivered_today = (
        db.query(Order)
        .filter(
            Order.delivered_at >= today_start,
            Order.status == "delivered",
        )
        .count()
    )

    products_active = db.query(Product).filter(Product.is_active.is_(True)).count()

    products_all = db.query(Product).filter(Product.is_active.is_(True)).all()
    low_stock = []
    for p in products_all:
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
                StockMovement.type.in_(["out", "production"]),
            )
            .with_entities(StockMovement.quantity)
            .all()
        )
        balance = sum(q[0] for q in total_in) - sum(q[0] for q in total_out)
        if balance < 5:
            low_stock.append(
                {
                    "id": p.id,
                    "name": p.name,
                    "balance": balance,
                    "unit": p.unit,
                }
            )

    recent_orders = (
        db.query(Order)
        .order_by(Order.created_at.desc())
        .limit(5)
        .all()
    )

    return {
        "orders_today": orders_today,
        "pending_payments": pending_payments,
        "delivered_today": delivered_today,
        "products_active": products_active,
        "low_stock": low_stock,
        "recent_orders": [
            {
                "id": o.id,
                "customer_name": o.customer_name,
                "payment_status": o.payment_status,
                "status": o.status,
                "created_at": o.created_at.isoformat(),
            }
            for o in recent_orders
        ],
    }
