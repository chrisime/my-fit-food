from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.models.order import Order, OrderItem
from app.models.product import Product
from app.models.stock import StockMovement
from app.models.user import User
from app.schemas.order import OrderCreate, OrderOut, OrderUpdate, PaymentUpdate
from app.services.crud import get_or_404
from app.ws.manager import notify_clients

router = APIRouter(prefix="/orders", tags=["orders"])


def _build_items(db: Session, items_data: list):
    items = []
    for item_in in items_data:
        product = get_or_404(db, Product, item_in.product_id, f"Product {item_in.product_id} not found")
        items.append(
            OrderItem(
                product_id=product.id,
                quantity=item_in.quantity,
                unit_price=product.price,
                is_free=item_in.is_free,
            )
        )
    return items


@router.get("/", response_model=list[OrderOut])
def list_orders(
    status: str | None = None,
    payment_status: str | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = db.query(Order)
    if status:
        q = q.filter(Order.status == status)
    if payment_status:
        q = q.filter(Order.payment_status == payment_status)
    return q.order_by(Order.created_at.desc()).all()


@router.post("/", response_model=OrderOut, status_code=201)
def create_order(
    body: OrderCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    order = Order(
        customer_name=body.customer_name,
        customer_phone=body.customer_phone,
        address_street=body.address_street,
        address_neighborhood=body.address_neighborhood,
        address_city=body.address_city,
        notes=body.notes,
        payment_status=body.payment_status,
        created_by=user.id,
        items=_build_items(db, body.items),
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


@router.put("/{order_id}", response_model=OrderOut)
def update_order(
    order_id: int,
    body: OrderUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    order = get_or_404(db, Order, order_id, "Order not found")
    if order.payment_status != "pending":
        raise HTTPException(status_code=400, detail="Só é possível editar pedidos pendentes")

    order.notes = body.notes
    order.items.clear()
    db.flush()

    order.items = _build_items(db, body.items)

    db.commit()
    db.refresh(order)
    return order


@router.delete("/{order_id}", status_code=204)
def delete_order(
    order_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    order = get_or_404(db, Order, order_id, "Order not found")
    if order.payment_status != "pending":
        raise HTTPException(status_code=400, detail="Só é possível excluir pedidos pendentes")
    db.delete(order)
    db.commit()


@router.patch("/{order_id}/payment", response_model=OrderOut)
def update_payment(
    order_id: int,
    body: PaymentUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    order = get_or_404(db, Order, order_id, "Order not found")
    order.payment_status = body.payment_status
    db.commit()
    db.refresh(order)
    return order


@router.patch("/{order_id}/reverse-payment", response_model=OrderOut)
def reverse_payment(
    order_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_role("admin")),
):
    order = get_or_404(db, Order, order_id, "Order not found")
    order.payment_status = "pending"
    db.commit()
    db.refresh(order)
    return order


@router.patch("/{order_id}/reverse-delivery", response_model=OrderOut)
def reverse_delivery(
    order_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("admin")),
):
    order = get_or_404(db, Order, order_id, "Order not found")
    if order.status != "delivered":
        raise HTTPException(status_code=400, detail="Order is not delivered")

    movements = (
        db.query(StockMovement)
        .filter(
            StockMovement.reference_type == "order",
            StockMovement.reference_id == order.id,
            StockMovement.type == "out",
            StockMovement.reversed.is_(False),
        )
        .all()
    )
    for m in movements:
        m.reversed = True

    order.status = "pending"
    order.delivered_at = None
    db.commit()
    db.refresh(order)
    notify_clients("stock_updated", {"order_id": order.id})
    return order


@router.patch("/{order_id}/deliver", response_model=OrderOut)
def deliver_order(
    order_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("admin")),
):
    order = get_or_404(db, Order, order_id, "Order not found")
    if order.status == "delivered":
        raise HTTPException(status_code=400, detail="Order already delivered")

    for item in order.items:
        movement = StockMovement(
            product_id=item.product_id,
            type="out",
            quantity=item.quantity,
            reference_type="order",
            reference_id=order.id,
            notes=f"Entrega do pedido #{order.id} - {order.customer_name}",
            created_by=user.id,
        )
        db.add(movement)

    order.status = "delivered"
    order.delivered_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(order)
    notify_clients("stock_updated", {"order_id": order.id})
    return order
