from enum import StrEnum


class UserRole(StrEnum):
    ADMIN = "admin"
    SALES = "sales"
    KITCHEN = "kitchen"


class ProductCategory(StrEnum):
    MEAL_BOX = "meal_box"
    SIDE_DISH = "side_dish"
    JUICE = "juice"
    BROWNIE = "brownie"
    BROTH = "broth"


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
