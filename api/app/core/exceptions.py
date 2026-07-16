from enum import IntEnum
from fastapi import HTTPException


class ErrorCode(IntEnum):
    INVALID_CREDENTIALS = 1001
    FORBIDDEN = 1002
    TOKEN_EXPIRED = 1003
    NOT_FOUND = 1004

    ORDER_NOT_PENDING = 2001
    ORDER_CANNOT_DELETE = 2002
    ORDER_PAYMENT_REVERT = 2003
    ORDER_NOT_DELIVERED = 2004
    ORDER_ALREADY_DELIVERED = 2005

    PRODUCT_HAS_LINKS = 3001

    STOCK_EXPIRY_REQUIRED = 4001
    STOCK_PRODUCT_NOT_FOUND = 4002

    CUSTOMER_NOT_FOUND = 5001

    USERNAME_DUPLICATE = 9001
    USER_SELF_DELETE = 9002
    USER_NOT_FOUND = 9003


class AppException(HTTPException):
    def __init__(self, status_code: int, code: int, detail: str):
        self.code = code
        super().__init__(status_code=status_code, detail=detail)
