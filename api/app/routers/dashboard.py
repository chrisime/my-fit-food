from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.order import Order
from app.models.product import Product
from app.models.user import User
from app.services.stock import compute_stock_balance

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

    balance = compute_stock_balance(db)
    low_stock = [
        {
            "id": b["product_id"],
            "name": b["product_name"],
            "balance": b["balance"],
            "unit": b["unit"],
        }
        for b in balance
        if b["balance"] < 5
    ]

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
