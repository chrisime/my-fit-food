from datetime import datetime

from pydantic import BaseModel

from app.schemas.datetime import TzDatetime


class BatchExpiresAtUpdate(BaseModel):
    movement_ids: list[int]
    expires_at: datetime


class StockMovementOut(BaseModel):
    id: int
    product_id: int
    type: str
    quantity: int
    order_id: int | None = None
    notes: str | None
    expires_at: TzDatetime | None = None
    created_by: int
    created_at: TzDatetime
    reversed: bool = False

    model_config = {"from_attributes": True}


class ProductionCreate(BaseModel):
    product_id: int
    quantity: int
    type: str = "in"
    notes: str | None = None
    expires_at: str | None = None


class ProductionOut(BaseModel):
    id: int
    product_id: int
    notes: str | None
    created_by: int
    created_at: TzDatetime

    model_config = {"from_attributes": True}
