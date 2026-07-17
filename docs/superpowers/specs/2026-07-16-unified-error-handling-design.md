# Unified Error Handling — Design Spec

## Ziel
Einheitliche Fehlerbehandlung über den gesamten Stack: Backend wirft Exceptions mit strukturierten Codes, Frontend extrahiert und zeigt sie mittels Oruga-Notifications.

## Backend

### AppException Klasse
`api/app/core/exceptions.py` — Basis-Exception, die einen internen `code` (Integer) mitführt.

```python
class AppException(HTTPException):
    def __init__(self, status_code: int, code: int, detail: str):
        self.code = code
        super().__init__(status_code=status_code, detail=detail)
```

### Error Codes (IntEnum)

| Code | Name | HTTP | Category |
|------|------|------|----------|
| 1001 | INVALID_CREDENTIALS | 401 | Auth |
| 1002 | FORBIDDEN | 403 | Auth |
| 1003 | TOKEN_EXPIRED | 401 | Auth |
| 1004 | NOT_FOUND | 404 | General |
| 2001 | ORDER_NOT_PENDING | 400 | Orders |
| 2002 | ORDER_CANNOT_DELETE | 400 | Orders |
| 2003 | ORDER_PAYMENT_REVERT | 400 | Orders |
| 2004 | ORDER_NOT_DELIVERED | 400 | Orders |
| 2005 | ORDER_ALREADY_DELIVERED | 400 | Orders |
| 3001 | PRODUCT_HAS_LINKS | 409 | Products |
| 4001 | STOCK_EXPIRY_REQUIRED | 400 | Stock |
| 4002 | STOCK_PRODUCT_NOT_FOUND | 404 | Stock |
| 5001 | CUSTOMER_NOT_FOUND | 404 | Customers |
| 9001 | USERNAME_DUPLICATE | 400 | Users |
| 9002 | USER_SELF_DELETE | 400 | Users |
| 9003 | USER_NOT_FOUND | 404 | Users |

### Global Exception Handler
In `api/app/main.py`:
- `AppException` → `{"detail": ..., "code": app_code, "status_code": ...}`
- `HTTPException` → `{"detail": ..., "code": http_status, "status_code": ...}`
- `Exception` (generic) → `{"detail": "Interner Serverfehler", "code": 0, "status_code": 500}`

### Migration
Alle `raise HTTPException(...)` in Services, Routern und Deps durch `raise AppException(code=ErrorCode.XXX, ...)` ersetzen.

## Frontend

### AppError Klasse
`web/src/types/error.ts` — Frontend-Äquivalent mit `detail`, `code`, `statusCode`.

### api.ts
Bei `!res.ok` → `res.json()` parsen, `AppError(detail, code, statusCode)` werfen.

### useToast Composable
`web/src/composables/useToast.ts` — Kapselt Orugas `oruga.notification.open()`.
- `toast(message, variant, duration)` — generisch
- `toastError(err)` — leitet aus `statusCode` die Variant ab (>=500 → `warning`, sonst `danger`)

### Views
Alle 9 Views erhalten try/catch um sämtliche API-Calls. Lokale Toast-Implementierungen und `alert()`-Aufrufe werden durch `useToast()` ersetzt.
