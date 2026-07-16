from sqlalchemy.orm import Session

from app.core.exceptions import AppException, ErrorCode
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate
from app.services.crud import create_from_schema, get_or_404, update_from_schema


def list_products(db: Session, active_only: bool = True) -> list[Product]:
    q = db.query(Product)
    if active_only:
        q = q.filter(Product.is_active.is_(True))
    return q.order_by(Product.name).all()


def create_product(db: Session, body: ProductCreate) -> Product:
    return create_from_schema(db, Product, body)


def update_product(db: Session, product_id: int, body: ProductUpdate) -> Product:
    return update_from_schema(db, Product, product_id, body, "Product not found")


def delete_product(db: Session, product_id: int) -> None:
    product = get_or_404(db, Product, product_id, "Product not found")
    db.delete(product)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise AppException(
            409,
            ErrorCode.PRODUCT_HAS_LINKS,
            "Product has linked orders or movements. Disable it instead of deleting.",
        )
