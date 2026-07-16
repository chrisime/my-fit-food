# Stock Date Simplification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Simplify FE date logic by having the BE return YYYY-MM-DD strings instead of ISO datetimes.

**Architecture:** BE `compute_stock_balance()` returns `expires_at` as date-only string + removes `expired` field. FE replaces UTC-heavy `weeksUntil()` with local Date constructors.

**Tech Stack:** FastAPI/Python, Vue 3/TypeScript

## Global Constraints

- No DB migration needed
- BC: FE expects YYYY-MM-DD from balance endpoint (deployed together)
- `CozinhaView.vue`/`ExpedicaoView.vue` — unchanged (no batch dates used)

---

### Task 1: BE — change `compute_stock_balance()` output

**Files:**
- Modify: `api/app/services/stock.py:135-151`

**Interfaces:**
- Consumes: existing `_utc()` helper, `g["date"]` (already YYYY-MM-DD)
- Produces: batch dict with `"expires_at": "2026-07-20"` (string, no T), no `"expired"` key

- [ ] **Replace response dict**

Current (lines 135-151):
```python
        result.append({
            "product_id": p.id,
            "product_name": p.name,
            "unit": p.unit,
            "balance": balance,
            "batches": [
                {
                    "date": g["date"],
                    "lot_ids": g["lot_ids"],
                    "quantity": g["quantity"],
                    "expires_at": g["expires_at"].isoformat(),
                    "expired": g["expires_at"] <= now,
                }
                for g in batches
                if g["quantity"] > 0
            ],
        })
    return result
```

Replace with:
```python
        result.append({
            "product_id": p.id,
            "product_name": p.name,
            "unit": p.unit,
            "balance": balance,
            "batches": [
                {
                    "date": g["date"],
                    "lot_ids": g["lot_ids"],
                    "quantity": g["quantity"],
                    "expires_at": g["date"],
                }
                for g in batches
                if g["quantity"] > 0
            ],
        })
    return result
```

- [ ] **Remove unused `now` variable**

Line 100: `now = datetime.now(timezone.utc)` — remove this line (no longer referenced)

- [ ] **Remove unused import if needed**

If `now` was the only user of `timezone` from line 1 (`from datetime import datetime, timezone`), keep `timezone` — still used in `create_production()` line 24, `deliver_order()` line 75.

- [ ] **Verify with build**

Run: `source api/.venv/bin/activate && python -c "from app.services.stock import compute_stock_balance; print('OK')"`

- [ ] **Commit**

```bash
git add api/app/services/stock.py
git commit -m "refactor: return expires_at as date-only, remove expired field"
```

---

### Task 2: FE — simplify `weeksUntil()` and related code

**Files:**
- Modify: `web/src/views/StockView.vue:25-31` (interface), `:72` (startEdit), `:91-112` (fmtDate/weeksUntil/expiryClass)

**Interfaces:**
- Consumes: `expires_at` as YYYY-MM-DD string from balance endpoint
- Produces: same UI with less complex date math

- [ ] **Update `Batch` interface — remove `expired`**

```typescript
interface Batch {
  date: string
  lot_ids: number[]
  quantity: number
  expires_at: string | null
}
```

- [ ] **Simplify `startEdit()` — remove `.split('T')[0]`**

```typescript
function startEdit(batch: Batch) {
  editingBatch.value = batch
  editExpiresAt.value = batch.expires_at || ''
  showEditModal.value = true
}
```

- [ ] **Simplify `fmtDate()` — remove T-split**

```typescript
function fmtDate(dateStr: string | null): string {
  if (!dateStr) return '—'
  return dateStr.split('-').reverse().join('/')
}
```

- [ ] **Simplify `weeksUntil()` — local Date constructors**

```typescript
function weeksUntil(dateStr: string | null): number {
  if (!dateStr) return Infinity
  const [y, m, d] = dateStr.split('-').map(Number)
  const exp = new Date(y, m - 1, d)
  const today = new Date(new Date().getFullYear(), new Date().getMonth(), new Date().getDate())
  return (exp.getTime() - today.getTime()) / (1000 * 60 * 60 * 24 * 7)
}
```

No change to `expiryClass()` — same logic, still calls `weeksUntil()`, just the called function is simpler.

- [ ] **Remove unused import if applicable**

Check `import { ref, onMounted, onUnmounted, computed } from 'vue'` — all still used.

- [ ] **Verify with build**

Run: `pnpm build:web`

- [ ] **Commit**

```bash
git add web/src/views/StockView.vue
git commit -m "refactor: simplify weeksUntil with local Date constructors"
```
