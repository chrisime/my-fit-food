from sqlalchemy import Boolean, Float, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    price: Mapped[float] = mapped_column(Float)
    category: Mapped[str | None] = mapped_column(String(60), nullable=True)
    unit: Mapped[str] = mapped_column(String(20), default="porção")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
