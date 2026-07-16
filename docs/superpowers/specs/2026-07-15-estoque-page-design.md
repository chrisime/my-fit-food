# Estoque — Separate Stock Page

## Motivation

The stock modal inside `CozinhaView.vue` is the only place to view balances, register production, and adjust inventory. Moving it to its own route `/estoque` makes it accessible from any view, allows role-gated write access per function, and reduces complexity in `CozinhaView.vue`.

## New Route

```
/estoque  — roles: vendas (read-only), cozinha (write in), admin (write in/out)
```

Added to `web/src/router/index.ts` with `meta: { roles: ['vendas', 'cozinha', 'admin'] }`.

A nav link is added in `App.vue` visible to all authenticated users.

## Components

### New: `StockView.vue`

A single page with three sections:

1. **Saldo Atual** (balance table) — always visible, full width
   - Columns: Produto, Saldo, Necessário, Diferença
   - "Necessário" and "Diferença" columns only shown for cozinha/admin roles
   - Data from `GET /stock/balance`

2. **Produção** (production form) — toggle section, visible for cozinha + admin
   - Product selector, quantity, notes
   - Submits to `POST /production/`

3. **Ajuste Manual** (adjust form) — toggle section
   - Admin: type selector (in/out), product, quantity, notes → `POST /stock/adjust`
   - Cozinha: simplified, no type selector (always "in"), submits to `POST /stock/adjust`
   - Vendas: not shown

WebSocket `stock_updated` refreshes balance table.

### Modified: `CozinhaView.vue`

- Remove `showStockModal`, `showProdForm`, `showAdjustForm`, `prodProductId`, `prodQuantity`, `prodNotes`, `adjustProductId`, `adjustType`, `adjustQuantity`, `adjustNotes`
- Remove `submitProduction()`, `submitAdjust()`, `loadProducts()`, `productOptions`, `toast`/`showToast`
- Keep `stockBalance`, `fetchBalance()`, `neededByOrders`, `stockFor()`, `needsProduction()`
- `quickProduce()` removed (previously opened modal) — the "produzir" badge becomes a plain indicator or a router-link to `/estoque`
- Replace Estoque button `<button @click="showStockModal = true">` with `<router-link to="/estoque">`

### Modified: `ExpedicaoView.vue`

- Remove `showStock`, stock modal, `fetchBalance()` (keep `stockBalance` for delivery checks)
- Replace "Ver Estoque" button with `<router-link to="/estoque">`

## Backend Changes

### `POST /stock/adjust` — role relaxation

Current: `require_role("admin")` → only admin.
New: accepts `get_current_user`, then:
- `admin`: no restrictions (type "in" or "out")
- `cozinha`: only `type == "in"`, otherwise 403
- `vendas`/other: 403

## Data Flow

```
StockView.vue
  ├── on mount → GET /stock/balance
  ├── WebSocket stock_updated → refetch balance
  ├── Produção submit → POST /production/
  └── Ajuste submit → POST /stock/adjust

CozinhaView.vue (inline badges)
  ├── on mount → GET /stock/balance
  └── WebSocket stock_updated → refetch balance

ExpedicaoView.vue (delivery checks)
  ├── on mount → GET /stock/balance
  └── after deliver/reverse → refetch balance
```

## Files Changed

| File | Change |
|---|---|
| `web/src/views/StockView.vue` | **New** — main stock page |
| `web/src/views/CozinhaView.vue` | Remove modal & stock forms, link to `/estoque` |
| `web/src/views/ExpedicaoView.vue` | Remove stock modal, link to `/estoque` |
| `web/src/router/index.ts` | Add `/estoque` route |
| `web/src/App.vue` | Add nav link for Estoque |
| `api/app/routers/stock.py` | Relax role guard for cozinha (in only) |
