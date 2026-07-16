# Estoque Page — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extract stock functionality from CozinhaView modals into a dedicated `/estoque` page.

**Architecture:** New `StockView.vue` page with balance table, production form, and adjust form. Backend role guard on `/stock/adjust` relaxed to allow cozinha (type="in" only) and admin (both). CozinhaView and ExpedicaoView lose their modals and gain router-links to `/estoque`.

**Tech Stack:** Vue 3 + Pinia + Oruga v0.9 + TailwindCSS (frontend), FastAPI + SQLAlchemy + SQLite (backend)

## Global Constraints

- No testing framework setup — verify with `pnpm build:web` (typecheck + build)
- Oruga v0.9.x configured globally, never import `@oruga-ui/theme-oruga/style.css`
- Icons via `@mdi/font` (class `mdi mdi-*`)
- Role guard: cozinha can only create type="in" stock movements; admin can do both in/out
- Routes use `meta: { roles: [...] }` with route guard in `router/beforeEach`

---

### Task 1: Backend — Relax role guard on `POST /stock/adjust`

**Files:**
- Modify: `api/app/routers/stock.py:29-46`

**Interfaces:**
- Produces: `POST /stock/adjust` now accepts `cozinha` (type="in" only) and `admin` (both). Returns 403 for `vendas` or cozinha trying type="out".

- [ ] **Step 1: Adjust role guard in `stock.py`**

Replace `user: User = Depends(require_role("admin"))` with `user: User = Depends(get_current_user)` and add inline role check:

```python
@router.post("/adjust", response_model=StockMovementOut, status_code=201)
def adjust_stock(
    body: StockAdjust,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if user.role not in ("admin", "cozinha"):
        raise HTTPException(status_code=403, detail="Not allowed")
    if user.role == "cozinha" and body.type != "in":
        raise HTTPException(status_code=403, detail="Cozinha can only add stock (type 'in')")
    get_or_404(db, Product, body.product_id, "Product not found")
    movement = StockMovement(
        product_id=body.product_id,
        type=body.type,
        quantity=body.quantity,
        notes=body.notes or f"Ajuste manual ({body.type})",
        created_by=user.id,
    )
    db.add(movement)
    db.commit()
    db.refresh(movement)
    return movement
```

Also clean up the import: remove `require_role` (no longer used):
```python
from app.core.deps import get_current_user
```

- [ ] **Step 2: Verify API starts**

```bash
cd api && source .venv/bin/activate && python -c "from app.routers.stock import adjust_stock; print('OK')"
```

Expected: prints `OK`

- [ ] **Step 3: Commit**

```
git add api/app/routers/stock.py
git commit -m "feat: relax stock/adjust role guard for cozinha (in only)"
```

---

### Task 2: Create `StockView.vue`

**Files:**
- Create: `web/src/views/StockView.vue`

**Interfaces:**
- Consumes: `get('/stock/balance')`, `post('/production/', ...)`, `post('/stock/adjust', ...)`, `useWebSocket()` composable
- Produces: Full stock page at `/estoque`

- [ ] **Step 1: Create the component**

```vue
<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useWebSocket } from '@/composables/useWebSocket'
import { get, post } from '@/composables/api'

const role = ref(localStorage.getItem('role') || '')
const isAdmin = computed(() => role.value === 'admin')
const isCozinha = computed(() => role.value === 'cozinha')
const canWrite = computed(() => isAdmin.value || isCozinha.value)

const stockBalance = ref<{ product_id: number; product_name: string; balance: number; unit: string }[]>([])
const productOptions = ref<{ label: string; value: number }[]>([])

const showProdForm = ref(false)
const showAdjustForm = ref(false)

const prodProductId = ref(0)
const prodQuantity = ref(1)
const prodNotes = ref('')

const adjustProductId = ref(0)
const adjustType = ref<'in' | 'out'>('in')
const adjustQuantity = ref(1)
const adjustNotes = ref('')

const toast = ref<{ show: boolean; message: string; type: 'success' | 'error' }>({ show: false, message: '', type: 'success' })
let toastTimer: ReturnType<typeof setTimeout> | null = null

const { on, off } = useWebSocket()

function showToast(message: string, type: 'success' | 'error' = 'success') {
  toast.value = { show: true, message, type }
  if (toastTimer) clearTimeout(toastTimer)
  toastTimer = setTimeout(() => { toast.value.show = false }, 4000)
}

onMounted(async () => {
  await Promise.all([fetchBalance(), loadProducts()])
  on('stock_updated', fetchBalance)
})

onUnmounted(() => {
  off('stock_updated')
  if (toastTimer) clearTimeout(toastTimer)
})

async function loadProducts() {
  const products = await get<any[]>('/products/')
  productOptions.value = products.map((p: any) => ({ label: p.name, value: p.id }))
}

async function fetchBalance() {
  stockBalance.value = await get('/stock/balance')
}

async function submitProduction() {
  try {
    await post('/production/', {
      product_id: prodProductId.value,
      quantity: prodQuantity.value,
      notes: prodNotes.value,
    })
    prodProductId.value = 0
    prodQuantity.value = 1
    prodNotes.value = ''
    showProdForm.value = false
    await fetchBalance()
    showToast('Produção registrada')
  } catch {
    showToast('Erro ao registrar produção', 'error')
  }
}

async function submitAdjust() {
  try {
    await post('/stock/adjust', {
      product_id: adjustProductId.value,
      type: adjustType.value,
      quantity: adjustQuantity.value,
      notes: adjustNotes.value || undefined,
    })
    adjustProductId.value = 0
    adjustQuantity.value = 1
    adjustNotes.value = ''
    showAdjustForm.value = false
    await fetchBalance()
    showToast('Ajuste salvo com sucesso')
  } catch {
    showToast('Erro ao salvar ajuste', 'error')
  }
}
</script>

<template>
  <div>
    <div class="flex justify-between items-center mb-4">
      <h2 class="text-xl font-semibold">Estoque</h2>
    </div>

    <transition name="fade">
      <div
        v-if="toast.show"
        class="fixed top-4 right-4 text-white px-4 py-3 rounded shadow-lg z-50 text-sm"
        :class="toast.type === 'success' ? 'bg-green-600' : 'bg-red-600'"
      >
        {{ toast.message }}
      </div>
    </transition>

    <div class="space-y-6">
      <form v-if="showProdForm && canWrite" @submit.prevent="submitProduction" class="border rounded-lg p-4 space-y-3 bg-gray-50">
        <p class="text-sm font-semibold text-gray-600">Registrar Produção</p>
        <div class="flex gap-4">
          <o-field label="Produto" class="flex-1">
            <select v-model="prodProductId" class="w-full border rounded px-3 py-2 text-sm bg-white" required>
              <option :value="0" disabled>Selecione</option>
              <option v-for="p in productOptions" :key="p.value" :value="p.value">{{ p.label }}</option>
            </select>
          </o-field>
          <o-field label="Quantidade" class="w-48">
            <o-input v-model="prodQuantity" type="number" min="1" required />
          </o-field>
        </div>
        <o-field label="Observações">
          <o-input v-model="prodNotes" type="textarea" />
        </o-field>
        <button type="submit" class="bg-green-600 hover:bg-green-700 text-white text-sm font-semibold py-1.5 px-4 rounded">Salvar Produção</button>
      </form>

      <form v-if="showAdjustForm && canWrite" @submit.prevent="submitAdjust" class="border rounded-lg p-4 space-y-3 bg-gray-50">
        <p class="text-sm font-semibold text-gray-600">Ajuste de Estoque</p>
        <div class="flex gap-4">
          <o-field label="Produto" class="flex-1">
            <select v-model="adjustProductId" class="w-full border rounded px-3 py-2 text-sm bg-white" required>
              <option :value="0" disabled>Selecione</option>
              <option v-for="p in productOptions" :key="p.value" :value="p.value">{{ p.label }}</option>
            </select>
          </o-field>
          <o-field v-if="isAdmin" label="Tipo" class="w-32">
            <select v-model="adjustType" class="w-full border rounded px-3 py-2 text-sm bg-white">
              <option value="in">Entrada</option>
              <option value="out">Saída</option>
            </select>
          </o-field>
          <o-field v-else label="Tipo" class="w-32">
            <div class="w-full border rounded px-3 py-2 text-sm bg-gray-100 text-gray-500">Entrada</div>
          </o-field>
          <o-field label="Qtd" class="w-32">
            <o-input v-model="adjustQuantity" type="number" min="1" required />
          </o-field>
        </div>
        <o-field label="Motivo">
          <o-input v-model="adjustNotes" type="textarea" placeholder="Ex: inventário, compra, quebra..." />
        </o-field>
        <button type="submit" class="bg-green-600 hover:bg-green-700 text-white text-sm font-semibold py-1.5 px-4 rounded">Salvar Ajuste</button>
      </form>

      <div>
        <p class="text-sm font-semibold text-gray-600 mb-2">Saldo Atual</p>
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b text-left">
              <th class="py-2">Produto</th>
              <th class="py-2 text-right">Saldo</th>
              <th class="py-2 text-right">Necessário</th>
              <th class="py-2 text-right">Diferença</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in stockBalance" :key="item.product_id" class="border-b hover:bg-gray-50">
              <td class="py-2">{{ item.product_name }}</td>
              <td class="py-2 text-right font-mono" :class="item.balance < 0 ? 'text-red-600' : 'text-green-700'">{{ item.balance }} {{ item.unit }}</td>
              <td class="py-2 text-right font-mono">—</td>
              <td class="py-2 text-right font-mono">—</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-if="canWrite" class="flex justify-center gap-4 pt-2 border-t">
        <button
          type="button"
          :title="showProdForm ? 'Fechar produção' : 'Produzir'"
          class="p-2 rounded-full hover:bg-gray-200"
          :class="showProdForm ? 'text-green-600 bg-green-100' : 'text-gray-600'"
          @click="showProdForm = !showProdForm"
        ><i class="mdi mdi-plus-circle text-2xl"></i></button>
        <button
          type="button"
          :title="showAdjustForm ? 'Fechar ajuste' : 'Ajustar'"
          class="p-2 rounded-full hover:bg-gray-200"
          :class="showAdjustForm ? 'text-green-600 bg-green-100' : 'text-gray-600'"
          @click="showAdjustForm = !showAdjustForm"
        ><i class="mdi mdi-tune text-2xl"></i></button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
```

- [ ] **Step 2: Verify build passes**

```bash
cd web && pnpm build:web
```

Expected: Build succeeds, no type errors.

- [ ] **Step 3: Commit**

```
git add web/src/views/StockView.vue
git commit -m "feat: create StockView page with balance, production, and adjust"
```

---

### Task 3: Add route + nav link for `/estoque`

**Files:**
- Modify: `web/src/router/index.ts`
- Modify: `web/src/App.vue`

**Interfaces:**
- Consumes: `StockView.vue` from Task 2
- Produces: Route `/estoque` accessible for vendas/cozinha/admin. Nav link visible to all authenticated users.

- [ ] **Step 1: Add route in `router/index.ts`**

Add after the `/produtos` route:

```ts
{
  path: '/estoque',
  name: 'estoque',
  component: () => import('@/views/StockView.vue'),
  meta: { roles: ['vendas', 'cozinha', 'admin'] },
},
```

- [ ] **Step 2: Add nav link in `App.vue`**

Add between the Produtos link and the dashboard links:

```html
<router-link to="/estoque" class="px-3 py-1.5 rounded hover:bg-green-600 font-medium">Estoque</router-link>
```

This link needs no `v-if` since it's visible to all authenticated users (all roles).

- [ ] **Step 3: Verify build passes**

```bash
cd web && pnpm build:web
```

Expected: Build succeeds.

- [ ] **Step 4: Commit**

```
git add web/src/router/index.ts web/src/App.vue
git commit -m "feat: add /estoque route and nav link"
```

---

### Task 4: Clean up `CozinhaView.vue` — remove stock modal

**Files:**
- Modify: `web/src/views/CozinhaView.vue`

- [ ] **Step 1: Remove stock-related refs, functions, and modal from CozinhaView**

Changes to the `<script setup>` section:
- Remove these refs: `showStockModal`, `productOptions`, `showProdForm`, `prodProductId`, `prodQuantity`, `prodNotes`, `showAdjustForm`, `adjustProductId`, `adjustType`, `adjustQuantity`, `adjustNotes`, `toast`, `toastTimer`
- Remove functions: `loadProducts`, `submitProduction`, `submitAdjust`, `showToast`
- Change `onMounted` — remove `loadProducts()` call (keep `fetchOrders()` and `fetchBalance()`)
- Remove `onUnmounted` toast cleanup (keep `off('stock_updated')` and timer cleanup)
- Remove `quickProduce` function (was tied to opening modal)
- Keep: `stockBalance`, `fetchBalance`, `neededByOrders`, `stockFor`, `needsProduction`

Changes to `<template>`:
- Remove the entire `<o-modal>` block
- Remove the `<transition name="fade">` toast block
- Remove the `import { post }` from api (only `get` needed now)
- Replace the Estoque button with a router-link

- [ ] **Step 2: Write the cleaned-up component**

Replace the entire file content with:

```vue
<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useOrderStore } from '@/stores/orders'
import { useWebSocket } from '@/composables/useWebSocket'
import { get } from '@/composables/api'

const store = useOrderStore()
const { on, off } = useWebSocket()

const stockBalance = ref<{ product_id: number; product_name: string; balance: number; unit: string }[]>([])

onMounted(async () => {
  await Promise.all([store.fetchOrders(), fetchBalance()])
  on('stock_updated', () => {
    store.fetchOrders()
    fetchBalance()
  })
})

onUnmounted(() => {
  off('stock_updated')
})

async function fetchBalance() {
  stockBalance.value = await get('/stock/balance')
}

const paidOrders = computed(() => store.orders.filter((o) => o.payment_status === 'paid' && o.status !== 'delivered'))
const pendingOrders = computed(() => store.orders.filter((o) => o.payment_status === 'pending' && o.status !== 'delivered'))

const neededByOrders = computed(() => {
  const map: Record<number, number> = {}
  for (const order of paidOrders.value) {
    for (const item of order.items) {
      map[item.product_id] = (map[item.product_id] || 0) + item.quantity
    }
  }
  return map
})

function stockFor(productId: number): { balance: number; unit: string } {
  const found = stockBalance.value.find((s) => s.product_id === productId)
  return found ? { balance: found.balance, unit: found.unit } : { balance: 0, unit: 'un' }
}

function needsProduction(productId: number, qty: number): boolean {
  const s = stockFor(productId)
  return s.balance < qty
}
</script>

<template>
  <div>
    <div class="flex justify-between items-center mb-4">
      <h2 class="text-xl font-semibold">Cozinha</h2>
      <router-link to="/estoque" class="bg-gray-200 hover:bg-gray-300 text-gray-700 font-semibold py-2 px-3 rounded text-sm">Estoque</router-link>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <div>
        <h3 class="font-semibold text-red-700 mb-2">🟡 Pendentes (Aguardando Pagamento)</h3>
        <div
          v-for="order in pendingOrders"
          :key="order.id"
          class="border-2 border-red-300 bg-red-50 rounded-lg p-4 mb-3 shadow-sm"
        >
          <p class="font-bold">{{ order.customer_name }}</p>
          <p class="text-sm text-gray-500">{{ order.items.length }} item(ns)</p>
        </div>
        <p v-if="!pendingOrders.length" class="text-gray-400 text-sm">Nenhum pedido pendente</p>
      </div>

      <div>
        <h3 class="font-semibold text-green-700 mb-2">🟢 Autorizados (Pagos)</h3>
        <div
          v-for="order in paidOrders"
          :key="order.id"
          class="border-2 border-green-500 bg-green-50 rounded-lg p-4 mb-3 shadow-sm"
        >
          <p class="font-bold">{{ order.customer_name }}</p>
          <p v-if="order.address_street || order.address_neighborhood || order.address_city" class="text-xs text-gray-500 mt-1">
            {{ [order.address_street, order.address_neighborhood, order.address_city].filter(Boolean).join(' — ') }}
          </p>
          <p v-if="order.notes" class="text-xs text-gray-500 italic mt-1">Obs: {{ order.notes }}</p>
          <div class="text-sm mt-2 space-y-1">
            <div v-for="item in order.items" :key="item.id" class="flex items-center justify-between gap-2">
              <span>{{ item.quantity }}x {{ item.product_name || 'Produto #' + item.product_id }}</span>
              <span
                class="text-xs font-semibold px-2 py-0.5 rounded whitespace-nowrap"
                :class="needsProduction(item.product_id, item.quantity) ? 'bg-yellow-100 text-yellow-800' : 'bg-green-100 text-green-800'"
              >
                <template v-if="needsProduction(item.product_id, item.quantity)">
                  produzir (estoque: {{ stockFor(item.product_id).balance }})
                </template>
                <template v-else>
                  em estoque ({{ stockFor(item.product_id).balance }})
                </template>
              </span>
            </div>
          </div>
        </div>
        <p v-if="!paidOrders.length" class="text-gray-400 text-sm">Nenhum pedido autorizado</p>
      </div>
    </div>
  </div>
</template>
```

- [ ] **Step 3: Verify build passes**

```bash
cd web && pnpm build:web
```

Expected: Build succeeds.

- [ ] **Step 4: Commit**

```
git add web/src/views/CozinhaView.vue
git commit -m "refactor: remove stock modal from CozinhaView, link to /estoque"
```

---

### Task 5: Clean up `ExpedicaoView.vue` — remove stock modal

**Files:**
- Modify: `web/src/views/ExpedicaoView.vue`

- [ ] **Step 1: Remove stock modal from ExpedicaoView**

In the `<script>` section: remove the `showStock` ref (line 10).

In the `<template>` section:
- Remove the entire `<o-modal>` block (lines 62-85)
- Replace the "Ver Estoque" button with a router-link

- [ ] **Step 2: Write the edits**

In `<script>` remove:
```ts
const showStock = ref(false)
```

In `<template>`, replace:
```html
<button
  class="text-sm bg-gray-200 hover:bg-gray-300 font-semibold py-1.5 px-3 rounded"
  @click="showStock = true"
>
  Ver Estoque
</button>
```

With:
```html
<router-link to="/estoque" class="text-sm bg-gray-200 hover:bg-gray-300 font-semibold py-1.5 px-3 rounded">Ver Estoque</router-link>
```

Remove the entire `<o-modal>` block.

Keep everything else unchanged (stock balance data is still used for delivery checks).

- [ ] **Step 3: Verify build passes**

```bash
cd web && pnpm build:web
```

Expected: Build succeeds.

- [ ] **Step 4: Commit**

```
git add web/src/views/ExpedicaoView.vue
git commit -m "refactor: remove stock modal from ExpedicaoView, link to /estoque"
```

---

### Task 6: Verify full build

- [ ] **Step 1: Run full build**

```bash
cd web && pnpm build:web
```

Expected: No type errors, build completes successfully.

- [ ] **Step 2: Verify API starts**

```bash
cd api && source .venv/bin/activate && uvicorn app.main:app --port 8000
```

Expected: API starts without import errors.

- [ ] **Step 3: Final commit**

```
git add -A
git commit -m "feat: extract stock into dedicated /estoque page"
```
