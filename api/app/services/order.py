from sqlalchemy.orm import Session

from app.core.exceptions import AppException, ErrorCode
from app.models.order import Order, OrderItem
from app.models.product import Product
from app.schemas.order import OrderCreate, OrderUpdate
from app.services.crud import get_or_404


def _build_items(db: Session, items_data: list) -> list[OrderItem]:
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


def list_orders(
    db: Session,
    status: str | None = None,
    payment_status: str | None = None,
) -> list[Order]:
    q = db.query(Order)
    if status:
        q = q.filter(Order.status == status)
    if payment_status:
        q = q.filter(Order.payment_status == payment_status)
    return q.order_by(Order.created_at.desc()).all()


def create_order(db: Session, body: OrderCreate, user_id: int) -> Order:
    order = Order(
        customer_name=body.customer_name,
        customer_phone=body.customer_phone,
        address_street=body.address_street,
        address_neighborhood=body.address_neighborhood,
        address_city=body.address_city,
        notes=body.notes,
        payment_status=body.payment_status,
        created_by=user_id,
        items=_build_items(db, body.items),
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


def update_order(db: Session, order_id: int, body: OrderUpdate) -> Order:
    order = get_or_404(db, Order, order_id, "Order not found")
    if order.payment_status != "pending":
        raise AppException(400, ErrorCode.ORDER_NOT_PENDING, "Only pending orders can be edited")
    order.notes = body.notes
    order.items.clear()
    db.flush()
    order.items = _build_items(db, body.items)
    db.commit()
    db.refresh(order)
    return order


def delete_order(db: Session, order_id: int) -> None:
    order = get_or_404(db, Order, order_id, "Order not found")
    if order.payment_status != "pending":
        raise AppException(400, ErrorCode.ORDER_CANNOT_DELETE, "Only pending orders can be deleted")
    db.delete(order)
    db.commit()


def update_payment(db: Session, order_id: int, payment_status: str) -> Order:
    order = get_or_404(db, Order, order_id, "Order not found")
    order.payment_status = payment_status
    db.commit()
    db.refresh(order)
    return order


def reverse_payment(db: Session, order_id: int) -> Order:
    order = get_or_404(db, Order, order_id, "Order not found")
    if order.status == "delivered":
        raise AppException(400, ErrorCode.ORDER_PAYMENT_REVERT, "Cannot reverse payment for a delivered order")
    order.payment_status = "pending"
    db.commit()
    db.refresh(order)
    return order
