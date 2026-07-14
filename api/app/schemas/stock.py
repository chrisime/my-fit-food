from datetime import datetime

from pydantic import BaseModel


class StockMovementOut(BaseModel):
    id: int
    product_id: int
    type: str
    quantity: float
    reference_type: str | None
    reference_id: int | None
    notes: str | None
    created_by: int
    created_at: datetime

    model_config = {"from_attributes": True}


class StockAdjust(BaseModel):
    product_id: int
    type: str = "in"
    quantity: float = 1
    notes: str | None = None


class ProductionCreate(BaseModel):
    product_id: int
    quantity: float
    notes: str | None = None


class ProductionOut(BaseModel):
    id: int
    product_id: int
    quantity: float
    notes: str | None
    created_by: int
    created_at: datetime

    model_config = {"from_attributes": True}
