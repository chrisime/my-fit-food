from fastapi import APIRouter, Depends

from app.core.deps import SessionUser, get_session
from app.schemas.order import OrderCreate, OrderOut, OrderUpdate
from app.services.order import (
    create_order,
    delete_order,
    list_orders,
    update_order,
)

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


@router.post("/update", response_model=OrderOut)
def update_order_endpoint(body: OrderUpdate, s: SessionUser = Depends(get_session)):
    return update_order(s.db, body.order_id, body)


@router.delete("/{order_id}", status_code=204)
def delete_order_endpoint(order_id: int, s: SessionUser = Depends(get_session)):
    delete_order(s.db, order_id)
