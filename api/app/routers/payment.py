from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import SessionUser, get_session, get_session_admin
from app.core.exceptions import AppException, ErrorCode
from app.models.order import Order
from app.schemas.order import OrderOut, PaymentBody
from app.services.crud import get_or_404

router = APIRouter(prefix="/payment", tags=["payment"])


@router.post("/", response_model=OrderOut)
def update_payment_endpoint(body: PaymentBody, s: SessionUser = Depends(get_session)):
    order = get_or_404(s.db, Order, body.order_id, "Order not found")
    order.payment_status = body.payment_status
    try:
        s.db.commit()
    except Exception:
        s.db.rollback()
        raise
    s.db.refresh(order)
    return order


@router.delete("/{order_id}", status_code=204)
def reverse_payment_endpoint(order_id: int, s: SessionUser = Depends(get_session_admin)):
    order = get_or_404(s.db, Order, order_id, "Order not found")
    if order.status == "delivered":
        raise AppException(400, ErrorCode.ORDER_PAYMENT_REVERT, "Cannot reverse payment for a delivered order")
    order.payment_status = "pending"
    try:
        s.db.commit()
    except Exception:
        s.db.rollback()
        raise
