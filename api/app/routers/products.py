from fastapi import APIRouter, Depends

from app.core.deps import SessionUser, get_session
from app.schemas.product import ProductCreate, ProductOut, ProductUpdate
from app.services.product import (
    create_product,
    delete_product,
    list_products,
    update_product,
)

router = APIRouter(prefix="/products", tags=["products"])


@router.get("/", response_model=list[ProductOut])
def list_products_endpoint(
    active_only: bool = True,
    s: SessionUser = Depends(get_session),
):
    return list_products(s.db, active_only)


@router.post("/", response_model=ProductOut, status_code=201)
def create_product_endpoint(body: ProductCreate, s: SessionUser = Depends(get_session)):
    return create_product(s.db, body)


@router.put("/{product_id}", response_model=ProductOut)
def update_product_endpoint(product_id: int, body: ProductUpdate, s: SessionUser = Depends(get_session)):
    return update_product(s.db, product_id, body)


@router.delete("/{product_id}", status_code=204)
def delete_product_endpoint(product_id: int, s: SessionUser = Depends(get_session)):
    delete_product(s.db, product_id)
