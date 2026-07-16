from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.product import Product
from app.models.production import Production
from app.models.stock import StockMovement


def _utc(dt: datetime) -> datetime:
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt


def create_production(db: Session, user_id: int, body) -> Production | StockMovement:
    product = db.query(Product).filter(Product.id == body.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if body.type == "in":
        if not body.expires_at:
            raise HTTPException(status_code=400, detail="Validade é obrigatória para entrada")
        expires_at = datetime.fromisoformat(body.expires_at).replace(tzinfo=timezone.utc)
    else:
        expires_at = None

    if body.type == "out":
        movement = StockMovement(
            product_id=body.product_id,
            type="out",
            quantity=body.quantity,
            notes=body.notes or "Ajuste manual (saída)",
            created_by=user_id,
        )
        db.add(movement)
        db.commit()
        db.refresh(movement)
        return movement

    prod = Production(
        product_id=body.product_id,
        notes=body.notes,
        created_by=user_id,
    )
    db.add(prod)
    db.flush()

    movement = StockMovement(
        product_id=body.product_id,
        type="in",
        quantity=body.quantity,
        notes=body.notes,
        expires_at=expires_at,
        created_by=user_id,
    )
    db.add(movement)
    db.commit()
    db.refresh(prod)
    return prod


def deliver_order(db: Session, user_id: int, order) -> None:
    for item in order.items:
        movement = StockMovement(
            product_id=item.product_id,
            type="out",
            quantity=item.quantity,
            order_id=order.id,
            notes=f"Entrega do pedido #{order.id} - {order.customer_name}",
            created_by=user_id,
        )
        db.add(movement)
    order.status = "delivered"
    order.delivered_at = datetime.now(timezone.utc)


def reverse_delivery(db: Session, order) -> None:
    movements = (
        db.query(StockMovement)
        .filter(
            StockMovement.order_id == order.id,
            StockMovement.type == "out",
            StockMovement.reversed.is_(False),
        )
        .all()
    )
    for m in movements:
        m.reversed = True
    order.status = "pending"
    order.delivered_at = None


def compute_stock_balance(db: Session, active_only: bool = True) -> list[dict]:
    products = db.query(Product)
    if active_only:
        products = products.filter(Product.is_active.is_(True))
    products = products.all()

    result = []

    for p in products:
        in_rows = (
            db.query(StockMovement.id, StockMovement.quantity, StockMovement.expires_at)
            .filter(StockMovement.product_id == p.id, StockMovement.type == "in", StockMovement.reversed.is_(False))
            .all()
        )
        out_qty = (
            db.query(func.coalesce(func.sum(StockMovement.quantity), 0))
            .filter(StockMovement.product_id == p.id, StockMovement.type == "out", StockMovement.reversed.is_(False))
            .scalar()
        )
        balance = sum(r.quantity for r in in_rows) - out_qty

        groups: dict[str, dict] = {}
        for r in in_rows:
            exp = _utc(r.expires_at)
            key = exp.strftime("%Y-%m-%d")
            if key not in groups:
                groups[key] = {"date": key, "lot_ids": [], "quantity": 0, "expires_at": exp}
            groups[key]["lot_ids"].append(r.id)
            groups[key]["quantity"] += r.quantity

        batches = sorted(groups.values(), key=lambda g: (g["date"], g["expires_at"]))

        remaining = out_qty
        for g in batches:
            if remaining <= 0:
                break
            deduct = min(g["quantity"], remaining)
            g["quantity"] -= deduct
            remaining -= deduct

        result.append({
            "product_id": p.id,
            "product_name": p.name,
            "unit": p.unit,
            "balance": balance,
            "batches": [
                {
                    "date": g["date"],
                    "lot_ids": g["lot_ids"],
                    "quantity": g["quantity"],
                    "expires_at": g["date"],
                }
                for g in batches
                if g["quantity"] > 0
            ],
        })
    return result
