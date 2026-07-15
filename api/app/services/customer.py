from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.schemas.customer import CustomerCreate, CustomerUpdate
from app.services.crud import create_from_schema, get_or_404, update_from_schema


def list_customers(db: Session) -> list[Customer]:
    return db.query(Customer).order_by(Customer.name).all()


def get_customer(db: Session, customer_id: int) -> Customer:
    return get_or_404(db, Customer, customer_id, "Customer not found")


def create_customer(db: Session, body: CustomerCreate) -> Customer:
    return create_from_schema(db, Customer, body)


def update_customer(db: Session, customer_id: int, body: CustomerUpdate) -> Customer:
    return update_from_schema(db, Customer, customer_id, body, "Customer not found")


def delete_customer(db: Session, customer_id: int) -> None:
    customer = get_or_404(db, Customer, customer_id, "Customer not found")
    db.delete(customer)
    db.commit()
