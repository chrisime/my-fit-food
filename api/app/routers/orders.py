from fastapi import APIRouter, Depends

from app.core.deps import SessionUser, get_session, get_session_admin
from app.core.exceptions import AppException, ErrorCode
from app.models.order import Order
from app.schemas.order import OrderCreate, OrderOut, OrderUpdate, PaymentUpdate
from app.services.order import (
    create_order,
    delete_order,
    list_orders,
    reverse_payment,
    update_order,
    update_payment,
)
from app.services.stock import deliver_order as stock_deliver
from app.services.stock import reverse_delivery as stock_reverse
from app.ws.manager import notify_clients

router = APIRouter(prefix="/orders", tags=["orders"])


@router.get("/", response_model=list[OrderOut])
def list_orders_endpoint(
    status: str | None = None,
    payment_status: str | None = None,
    s: SessionUser = Depends(get_session),
):
    return list_orders(s.db, status, payment_status)


@router.post("/", response_model=OrderOut, status_code=201)
def create_order_endpoint(body: OrderCreate, s: SessionUser = Depends(get_session)):
    return create_order(s.db, body, s.user.id)


@router.put("/{order_id}", response_model=OrderOut)
def update_order_endpoint(order_id: int, body: OrderUpdate, s: SessionUser = Depends(get_session)):
    return update_order(s.db, order_id, body)


@router.delete("/{order_id}", status_code=204)
def delete_order_endpoint(order_id: int, s: SessionUser = Depends(get_session)):
    delete_order(s.db, order_id)


@router.patch("/{order_id}/payment", response_model=OrderOut)
def update_payment_endpoint(order_id: int, body: PaymentUpdate, s: SessionUser = Depends(get_session)):
    return update_payment(s.db, order_id, body.payment_status)


@router.patch("/{order_id}/reverse-payment", response_model=OrderOut)
def reverse_payment_endpoint(order_id: int, s: SessionUser = Depends(get_session_admin)):
    return reverse_payment(s.db, order_id)


@router.patch("/{order_id}/reverse-delivery", response_model=OrderOut)
def rev_delivery(order_id: int, s: SessionUser = Depends(get_session_admin)):
    order = s.db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise AppException(404, ErrorCode.NOT_FOUND, "Order not found")
    if order.status != "delivered":
        raise AppException(400, ErrorCode.ORDER_NOT_DELIVERED, "Order is not delivered")
    stock_reverse(s.db, order)
    s.db.commit()
    s.db.refresh(order)
    notify_clients("stock_updated", {"order_id": order.id})
    return order


@router.patch("/{order_id}/deliver", response_model=OrderOut)
def deliver(order_id: int, s: SessionUser = Depends(get_session_admin)):
    order = s.db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise AppException(404, ErrorCode.NOT_FOUND, "Order not found")
    if order.status == "delivered":
        raise AppException(400, ErrorCode.ORDER_ALREADY_DELIVERED, "Order already delivered")
    stock_deliver(s.db, s.user.id, order)
    s.db.commit()
    s.db.refresh(order)
    notify_clients("stock_updated", {"order_id": order.id})
    return order
