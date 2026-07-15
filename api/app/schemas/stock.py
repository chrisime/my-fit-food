from datetime import date as date_type

from pydantic import BaseModel

from app.schemas.datetime import TzDatetime


class BatchExpiresAtUpdate(BaseModel):
    movement_ids: list[int]
    expires_at: date_type


class StockMovementOut(BaseModel):
    id: int
    product_id: int
    type: str
    quantity: float
    reference_type: str | None
    reference_id: int | None
    notes: str | None
    expires_at: TzDatetime | None = None
    created_by: int
    created_at: TzDatetime
    reversed: bool = False

    model_config = {"from_attributes": True}


class ProductionCreate(BaseModel):
    product_id: int
    quantity: float
    type: str = "in"
    notes: str | None = None
    expires_at: str | None = None


class ProductionOut(BaseModel):
    id: int
    product_id: int
    quantity: float
    notes: str | None
    created_by: int
    created_at: TzDatetime

    model_config = {"from_attributes": True}
