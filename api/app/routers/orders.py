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

router = APIRouter(prefix="/orders", tags=["orders"])


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
    items = []
    for item_in in body.items:
        product = db.query(Product).filter(Product.id == item_in.product_id).first()
        if not product:
            raise HTTPException(
                status_code=404,
                detail=f"Product {item_in.product_id} not found",
            )
        items.append(
            OrderItem(
                product_id=product.id,
                quantity=item_in.quantity,
                unit_price=product.price,
                is_free=item_in.is_free,
            )
        )
    order = Order(
        customer_name=body.customer_name,
        customer_phone=body.customer_phone,
        address_street=body.address_street,
        address_neighborhood=body.address_neighborhood,
        address_city=body.address_city,
        notes=body.notes,
        payment_status=body.payment_status,
        created_by=user.id,
        items=items,
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
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.payment_status != "pending":
        raise HTTPException(status_code=400, detail="Só é possível editar pedidos pendentes")

    order.notes = body.notes

    order.items.clear()
    db.flush()

    for item_in in body.items:
        product = db.query(Product).filter(Product.id == item_in.product_id).first()
        if not product:
            raise HTTPException(
                status_code=404,
                detail=f"Product {item_in.product_id} not found",
            )
        order.items.append(
            OrderItem(
                product_id=product.id,
                quantity=item_in.quantity,
                unit_price=product.price,
                is_free=item_in.is_free,
            )
        )

    db.commit()
    db.refresh(order)
    return order


@router.delete("/{order_id}", status_code=204)
def delete_order(
    order_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
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
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
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
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    order.payment_status = "pending"
    db.commit()
    db.refresh(order)
    return order


@router.patch("/{order_id}/reverse-delivery", response_model=OrderOut)
def reverse_delivery(
    order_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_role("admin")),
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.status != "delivered":
        raise HTTPException(status_code=400, detail="Order is not delivered")
    order.status = "pending"
    order.delivered_at = None
    db.commit()
    db.refresh(order)
    return order


@router.patch("/{order_id}/deliver", response_model=OrderOut)
def deliver_order(
    order_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("admin")),
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
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
    return order
