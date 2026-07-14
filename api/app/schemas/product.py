from pydantic import BaseModel


class ProductOut(BaseModel):
    id: int
    name: str
    description: str | None
    price: float
    category: str | None
    unit: str
    is_active: bool

    model_config = {"from_attributes": True}


class ProductCreate(BaseModel):
    name: str
    description: str | None = None
    price: float
    category: str | None = None
    unit: str = "porção"
    is_active: bool = True


class ProductUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    price: float | None = None
    category: str | None = None
    unit: str | None = None
    is_active: bool | None = None
