from pydantic import BaseModel

from app.schemas.datetime import TzDatetime


class CustomerCreate(BaseModel):
    name: str
    phone: str | None = None
    address_street: str | None = None
    address_neighborhood: str | None = None
    address_city: str | None = None
    address2_street: str | None = None
    address2_neighborhood: str | None = None
    address2_city: str | None = None
    notes: str | None = None


class CustomerUpdate(BaseModel):
    name: str | None = None
    phone: str | None = None
    address_street: str | None = None
    address_neighborhood: str | None = None
    address_city: str | None = None
    address2_street: str | None = None
    address2_neighborhood: str | None = None
    address2_city: str | None = None
    notes: str | None = None


class CustomerOut(BaseModel):
    id: int
    name: str
    phone: str | None
    address_street: str | None
    address_neighborhood: str | None
    address_city: str | None
    address2_street: str | None
    address2_neighborhood: str | None
    address2_city: str | None
    notes: str | None
    created_at: TzDatetime

    model_config = {"from_attributes": True}
