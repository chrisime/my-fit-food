from fastapi import APIRouter, Depends

from app.core.deps import SessionUser, get_session
from app.schemas.customer import CustomerCreate, CustomerOut, CustomerUpdate
from app.services.customer import (
    create_customer,
    delete_customer,
    get_customer,
    list_customers,
    update_customer,
)

router = APIRouter(prefix="/customers", tags=["customers"])


@router.get("/", response_model=list[CustomerOut])
def list_customers_endpoint(s: SessionUser = Depends(get_session)):
    return list_customers(s.db)


@router.get("/{customer_id}", response_model=CustomerOut)
def get_customer_endpoint(customer_id: int, s: SessionUser = Depends(get_session)):
    return get_customer(s.db, customer_id)


@router.post("/", response_model=CustomerOut, status_code=201)
def create_customer_endpoint(body: CustomerCreate, s: SessionUser = Depends(get_session)):
    return create_customer(s.db, body)


@router.put("/{customer_id}", response_model=CustomerOut)
def update_customer_endpoint(customer_id: int, body: CustomerUpdate, s: SessionUser = Depends(get_session)):
    return update_customer(s.db, customer_id, body)


@router.delete("/{customer_id}", status_code=204)
def delete_customer_endpoint(customer_id: int, s: SessionUser = Depends(get_session)):
    delete_customer(s.db, customer_id)
