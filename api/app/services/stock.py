from sqlalchemy.orm import Session

from app.models.product import Product
from app.models.stock import StockMovement


def compute_stock_balance(db: Session, active_only: bool = True):
    query = db.query(Product)
    if active_only:
        query = query.filter(Product.is_active.is_(True))
    products = query.all()

    result = []
    for p in products:
        total_in = (
            db.query(StockMovement)
            .filter(
                StockMovement.product_id == p.id,
                StockMovement.type == "in",
                StockMovement.reversed.is_(False),
            )
            .with_entities(StockMovement.quantity)
            .all()
        )
        total_out = (
            db.query(StockMovement)
            .filter(
                StockMovement.product_id == p.id,
                StockMovement.type == "out",
                StockMovement.reversed.is_(False),
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
