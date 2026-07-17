from pydantic import BaseModel

from fastapi import APIRouter, Depends

from app.core.deps import SessionUser, get_session_admin
from app.core.exceptions import AppException, ErrorCode
from app.models.order import Order
from app.schemas.order import OrderOut
from app.services.stock import deliver_order as stock_deliver
from app.services.stock import reverse_delivery as stock_reverse
from app.ws.manager import notify_clients

router = APIRouter(prefix="/deliver", tags=["deliver"])


class DeliverBody(BaseModel):
    order_id: int


@router.post("/", response_model=OrderOut)
def deliver_endpoint(body: DeliverBody, s: SessionUser = Depends(get_session_admin)):
    order = s.db.query(Order).filter(Order.id == body.order_id).first()
    if not order:
        raise AppException(404, ErrorCode.NOT_FOUND, "Order not found")
    if order.status == "delivered":
        raise AppException(400, ErrorCode.ORDER_ALREADY_DELIVERED, "Order already delivered")
    stock_deliver(s.db, s.user.id, order)
    s.db.commit()
    s.db.refresh(order)
    notify_clients("stock_updated", {"order_id": order.id})
    return order


@router.delete("/{order_id}", response_model=OrderOut)
def reverse_delivery_endpoint(order_id: int, s: SessionUser = Depends(get_session_admin)):
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
