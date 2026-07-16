from enum import StrEnum


class UserRole(StrEnum):
    ADMIN = "admin"
    SALES = "sales"
    KITCHEN = "kitchen"


class ProductCategory(StrEnum):
    MARMITA = "marmita"
    ACOMPANHAMENTO = "acompanhamento"
    SUCO = "suco"
    BROWNIE = "brownie"
    CALDO = "caldo"


class UnitType(StrEnum):
    UN = "un"
    SERVING = "serving"
    KG = "kg"
    L = "L"


class MovementType(StrEnum):
    IN = "in"
    OUT = "out"


class PaymentStatus(StrEnum):
    PENDING = "pending"
    PAID = "paid"


class OrderStatus(StrEnum):
    PENDING = "pending"
    DELIVERED = "delivered"
