# Unified Error Handling Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement end-to-end unified error handling — backend raises structured exceptions, frontend parses and displays via Oruga notifications.

**Architecture:** Custom `AppException(HTTPException)` with integer error codes; global exception handler in FastAPI; `AppError` class + `useToast` composable in Vue; all views wrapped in try/catch.

**Tech Stack:** FastAPI, Vue 3 + Oruga, Pinia

## Global Constraints
- No new npm/pip dependencies
- Follow existing code conventions (AGENTS.md)
- Use Oruga `oruga.notification.open()` programmatic API for toasts
- Portuguese error messages remain unchanged

---

### Task 1: Backend — AppException + ErrorCode + Exception Handler

**Files:**
- Create: `api/app/core/exceptions.py`
- Modify: `api/app/main.py`

**Produces:** `AppException` class, `ErrorCode(IntEnum)`, exception handlers in main.py

- [ ] **Create `api/app/core/exceptions.py`:**

```python
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
```

- [ ] **Add exception handlers to `api/app/main.py`:**

```python
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from fastapi import Request
from app.core.exceptions import AppException


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "code": exc.code, "status_code": exc.status_code},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "code": exc.status_code, "status_code": exc.status_code},
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "Interner Serverfehler", "code": 0, "status_code": 500},
    )
```

- [ ] **Commit**

---

### Task 2: Backend — Services zu AppException migrieren

**Files:**
- Modify: `api/app/services/crud.py`, `api/app/services/order.py`, `api/app/services/product.py`, `api/app/services/stock.py`, `api/app/services/user.py`

**Consumes:** `AppException`, `ErrorCode` from Task 1

- [ ] **`crud.py`:** Replace import and `get_or_404` raise:
```
from fastapi import HTTPException
→ from app.core.exceptions import AppException, ErrorCode

raise HTTPException(status_code=404, detail=detail)
→ raise AppException(status_code=404, code=ErrorCode.NOT_FOUND, detail=detail)
```

- [ ] **`order.py`:** Replace raises:
```python
from app.core.exceptions import AppException, ErrorCode

raise HTTPException(status_code=400, detail="Só é possível editar pedidos pendentes")
→ raise AppException(400, ErrorCode.ORDER_NOT_PENDING, "Só é possível editar pedidos pendentes")

raise HTTPException(status_code=400, detail="Só é possível excluir pedidos pendentes")
→ raise AppException(400, ErrorCode.ORDER_CANNOT_DELETE, "Só é possível excluir pedidos pendentes")

raise HTTPException(status_code=400, detail="Não é possível reverter pagamento de um pedido já entregue")
→ raise AppException(400, ErrorCode.ORDER_PAYMENT_REVERT, "Não é possível reverter pagamento de um pedido já entregue")
```

- [ ] **`product.py`:** Replace raise:
```python
from app.core.exceptions import AppException, ErrorCode

raise HTTPException(status_code=409, detail="Produto possui pedidos ou movimentações vinculadas. Desative-o em vez de excluir.")
→ raise AppException(409, ErrorCode.PRODUCT_HAS_LINKS, "Produto possui pedidos ou movimentações vinculadas. Desative-o em vez de excluir.")
```

- [ ] **`stock.py`:** Replace raises:
```python
from app.core.exceptions import AppException, ErrorCode

raise HTTPException(status_code=404, detail="Product not found")
→ raise AppException(404, ErrorCode.STOCK_PRODUCT_NOT_FOUND, "Product not found")

raise HTTPException(status_code=400, detail="Validade é obrigatória para entrada")
→ raise AppException(400, ErrorCode.STOCK_EXPIRY_REQUIRED, "Validade é obrigatória para entrada")
```

- [ ] **`user.py`:** Replace raises:
```python
from app.core.exceptions import AppException, ErrorCode

raise HTTPException(status_code=400, detail="Username already taken")
→ raise AppException(400, ErrorCode.USERNAME_DUPLICATE, "Username already taken")

raise HTTPException(status_code=400, detail="Não pode excluir a si mesmo")
→ raise AppException(400, ErrorCode.USER_SELF_DELETE, "Não pode excluir a si mesmo")

raise HTTPException(status_code=404, detail="User not found")
→ raise AppException(404, ErrorCode.USER_NOT_FOUND, "User not found")
```

- [ ] **Commit**

---

### Task 3: Backend — Router + Deps zu AppException migrieren

**Files:**
- Modify: `api/app/routers/auth.py`, `api/app/routers/orders.py`, `api/app/routers/stock.py`, `api/app/core/deps.py`

- [ ] **`auth.py`:** Replace raise + import:
```python
from app.core.exceptions import AppException, ErrorCode

raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
→ raise AppException(401, ErrorCode.INVALID_CREDENTIALS, "Invalid credentials")
```

- [ ] **`orders.py`:** Replace raises + import:
```python
from app.core.exceptions import AppException, ErrorCode

raise HTTPException(status_code=404, detail="Order not found")
→ raise AppException(404, ErrorCode.NOT_FOUND, "Order not found")

raise HTTPException(status_code=400, detail="Order is not delivered")
→ raise AppException(400, ErrorCode.ORDER_NOT_DELIVERED, "Order is not delivered")

raise HTTPException(status_code=400, detail="Order already delivered")
→ raise AppException(400, ErrorCode.ORDER_ALREADY_DELIVERED, "Order already delivered")
```

- [ ] **`stock.py`:** Replace raise + import:
```python
from app.core.exceptions import AppException, ErrorCode

raise HTTPException(status_code=404, detail="No movements found")
→ raise AppException(404, ErrorCode.NOT_FOUND, "No movements found")
```

- [ ] **`deps.py`:** Replace raises + import:
```python
from app.core.exceptions import AppException, ErrorCode

raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
→ raise AppException(401, ErrorCode.TOKEN_EXPIRED, "Invalid token")

raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
→ raise AppException(401, ErrorCode.INVALID_CREDENTIALS, "User not found")

raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Role '{role}' required")
→ raise AppException(403, ErrorCode.FORBIDDEN, f"Role '{role}' required")
```

- [ ] **Commit**

---

### Task 4: Frontend — AppError + api.ts + useToast

**Files:**
- Create: `web/src/types/error.ts`
- Modify: `web/src/composables/api.ts`
- Create: `web/src/composables/useToast.ts`

- [ ] **Create `web/src/types/error.ts`:**

```typescript
export class AppError extends Error {
  constructor(
    public detail: string,
    public code: number,
    public statusCode: number,
  ) {
    super(detail)
    this.name = 'AppError'
  }
}
```

- [ ] **Update `web/src/composables/api.ts`:** Add import, change error handling:

```typescript
import { AppError } from '@/types/error'

// In request():
  if (res.status === 401) {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    localStorage.removeItem('role')
    window.location.href = '/login'
    throw new AppError('Sessão expirada', 1003, 401)
  }
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new AppError(
      body.detail || 'Unbekannter Fehler',
      body.code ?? res.status,
      res.status,
    )
  }
```

- [ ] **Create `web/src/composables/useToast.ts`:**

```typescript
import { useProgrammatic } from '@oruga-ui/oruga-next'
import { AppError } from '@/types/error'

export function useToast() {
  function toast(message: string, variant: 'success' | 'danger' | 'warning' = 'danger', duration = 4000) {
    const { oruga } = useProgrammatic()
    oruga.notification.open({
      message,
      variant,
      duration,
      position: 'top-right',
    })
  }

  function toastError(err: unknown) {
    if (err instanceof AppError) {
      const variant = err.statusCode >= 500 ? 'warning' : 'danger'
      toast(err.detail, variant)
    } else {
      toast('Unbekannter Fehler', 'danger')
    }
  }

  return { toast, toastError }
}
```

- [ ] **Commit**

---

### Task 5: Frontend — VendasView + StockView

**Files:**
- Modify: `web/src/views/VendasView.vue`, `web/src/views/StockView.vue`

- [ ] **VendasView.vue:**
  - Add `import { useToast } from '@/composables/useToast'`
  - Add `import { AppError } from '@/types/error'`
  - Add `const { toast, toastError } = useToast()`
  - Remove local `toast` ref and `toastTimer`
  - Remove local `showToast()` function
  - Wrap `loadProducts()` in try/catch
  - Wrap `loadCustomers()` in try/catch
  - Wrap `openEditProduct(productId)`'s get call in try/catch
  - Change `deleteOrder()` catch to `toastError(e)`
  - Change `saveProduct()` catch to `toastError(e)`
  - Wrap `confirmPayment(orderId)` in try/catch
  - Remove `<transition name="fade">` toast div from template

- [ ] **StockView.vue:**
  - Add `import { useToast } from '@/composables/useToast'`
  - Add `import { AppError } from '@/types/error'`
  - Add `const { toast, toastError } = useToast()`
  - Remove local `toast` ref, `toastTimer`, `showToast()`
  - Wrap `loadProducts()` in try/catch
  - Wrap `fetchBalance()` in try/catch
  - Change `saveExpiresAt()` catch to `toastError(e)`
  - Change `submitMovement()` catch to `toastError(e)`
  - Wrap `store.fetchOrders()` in try/catch in onMounted
  - Remove `<transition name="fade">` toast div from template

- [ ] **Commit**

---

### Task 6: Frontend — ClientesView + ProdutosView + UsuariosView

**Files:**
- Modify: `web/src/views/ClientesView.vue`, `web/src/views/ProdutosView.vue`, `web/src/views/UsuariosView.vue`

- [ ] **ClientesView.vue:**
  - Import `useToast()`
  - Wrap `loadCustomers()` in try/catch
  - Wrap `save()` in try/catch
  - Change `deleteCustomer()` catch from `alert()` to `toastError(e)`

- [ ] **ProdutosView.vue:**
  - Import `useToast()`
  - Wrap `loadProducts()` in try/catch
  - Wrap `save()` in try/catch
  - Change `deleteProduct()` catch from `alert()` to `toastError(e)`
  - Wrap `toggleActive()` in try/catch

- [ ] **UsuariosView.vue:**
  - Import `useToast()`
  - Wrap `loadUsers()` in try/catch
  - Wrap `saveUser()` in try/catch
  - Change `deleteUser()` catch from `alert()` to `toastError(e)`

- [ ] **Commit**

---

### Task 7: Frontend — DashboardView + CozinhaView + ExpedicaoView + LoginView

**Files:**
- Modify: `web/src/views/DashboardView.vue`, `web/src/views/CozinhaView.vue`, `web/src/views/ExpedicaoView.vue`, `web/src/views/LoginView.vue`

- [ ] **DashboardView.vue:**
  - Import `useToast()`
  - Wrap `onMounted` handler in try/catch with `toastError`

- [ ] **CozinhaView.vue:**
  - Import `useToast()`
  - Wrap `onMounted`'s `store.fetchOrders()` and `fetchBalance()` in try/catch
  - Wrap `fetchBalance()` in try/catch

- [ ] **ExpedicaoView.vue:**
  - Import `useToast()`
  - Wrap `onMounted`'s `store.fetchOrders()` and `fetchBalance()` in try/catch
  - Wrap `deliverAndRefresh()` in try/catch
  - Wrap `reverseAndRefresh()` in try/catch

- [ ] **LoginView.vue:**
  - Import `useToast()`
  - Change `catch` from setting local `error` to `toastError(e)`
  - Remove local `error` ref and the `<p v-if="error">` template element

- [ ] **Commit**
