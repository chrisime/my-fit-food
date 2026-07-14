from datetime import datetime

from pydantic import BaseModel


class OrderItemIn(BaseModel):
    product_id: int
    quantity: int = 1
    is_free: bool = False


class OrderCreate(BaseModel):
    customer_name: str
    customer_phone: str | None = None
    address_street: str | None = None
    address_neighborhood: str | None = None
    address_city: str | None = None
    notes: str | None = None
    payment_status: str = "pending"
    items: list[OrderItemIn]


class OrderItemOut(BaseModel):
    id: int
    product_id: int
    quantity: int
    unit_price: float
    is_free: bool
    product_name: str | None = None

    model_config = {"from_attributes": True}


class OrderOut(BaseModel):
    id: int
    customer_name: str
    customer_phone: str | None
    address_street: str | None
    address_neighborhood: str | None
    address_city: str | None
    notes: str | None
    payment_status: str
    status: str
    created_by: int
    created_at: datetime
    delivered_at: datetime | None
    items: list[OrderItemOut]

    model_config = {"from_attributes": True}


class OrderUpdate(BaseModel):
    notes: str | None = None
    items: list[OrderItemIn]


class PaymentUpdate(BaseModel):
    payment_status: str
