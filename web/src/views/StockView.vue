<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useOrderStore } from '@/stores/orders'
import { useWebSocket } from '@/composables/useWebSocket'
import { get, post, patch } from '@/composables/api'
import { unitLabel } from '@/composables/labels'

const role = ref(localStorage.getItem('role') || '')
const isAdmin = computed(() => role.value === 'admin')
const isKitchen = computed(() => role.value === 'kitchen')
const canWrite = computed(() => isAdmin.value || isKitchen.value)

const store = useOrderStore()

const neededByOrders = computed(() => {
  const map: Record<number, number> = {}
  for (const order of store.orders.filter((o) => o.payment_status === 'paid' && o.status !== 'delivered')) {
    for (const item of order.items) {
      map[item.product_id] = (map[item.product_id] || 0) + item.quantity
    }
  }
  return map
})

interface Batch {
  date: string
  lot_ids: number[]
  quantity: number
  created_at: string
  expires_at: string | null
}

interface ProductStock {
  product_id: number
  product_name: string
  balance: number
  unit: string
  batches: Batch[]
}

const stockBalance = ref<ProductStock[]>([])
const expanded = ref<Set<number>>(new Set())
function toggle(id: number) {
  if (expanded.value.has(id)) expanded.value.delete(id)
  else expanded.value.add(id)
}
const productOptions = ref<{ label: string; value: number }[]>([])

const showForm = ref(false)
const formProductId = ref(0)
const formType = ref<'in' | 'out'>('in')
const formQuantity = ref(1)
const formNotes = ref('')
const formExpiresAt = ref('')

const toast = ref<{ show: boolean; message: string; type: 'success' | 'error' }>({ show: false, message: '', type: 'success' })
let toastTimer: ReturnType<typeof setTimeout> | null = null

const { on, off } = useWebSocket()

function showToast(message: string, type: 'success' | 'error' = 'success') {
  toast.value = { show: true, message, type }
  if (toastTimer) clearTimeout(toastTimer)
  toastTimer = setTimeout(() => { toast.value.show = false }, 4000)
}

const showEditModal = ref(false)
const editingBatch = ref<Batch | null>(null)
const editExpiresAt = ref('')
function startEdit(batch: Batch) {
  editingBatch.value = batch
  editExpiresAt.value = batch.expires_at || ''
  showEditModal.value = true
}
async function saveExpiresAt() {
  if (!editingBatch.value) return
  try {
    await patch('/stock/batch/expires-at', {
      movement_ids: editingBatch.value.lot_ids,
      expires_at: editExpiresAt.value,
    })
    showToast('Validade atualizada')
    showEditModal.value = false
    editingBatch.value = null
    await fetchBalance()
  } catch (e: any) {
    showToast(e.message, 'error')
  }
}

function fmtDate(dateStr: string | null): string {
  if (!dateStr) return '—'
  return dateStr.split('-').reverse().join('/')
}

function weeksUntil(dateStr: string | null): number {
  if (!dateStr) return Infinity
  const [y, m, d] = dateStr.split('-').map(Number)
  const exp = new Date(y, m - 1, d)
  const today = new Date(new Date().getFullYear(), new Date().getMonth(), new Date().getDate())
  return (exp.getTime() - today.getTime()) / (1000 * 60 * 60 * 24 * 7)
}

function expiryClass(dateStr: string | null): string {
  const w = weeksUntil(dateStr)
  if (w <= 0) return 'text-red-600 font-bold'
  if (w < 4) return 'text-red-600'
  if (w < 6) return 'text-yellow-600'
  if (w <= 8) return 'text-green-600'
  return 'text-green-700'
}

onMounted(async () => {
  await Promise.all([store.fetchOrders(), fetchBalance(), loadProducts()])
  on('stock_updated', () => {
    store.fetchOrders()
    fetchBalance()
  })
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

async function submitMovement() {
  if (!formProductId.value) { showToast('Selecione um produto', 'error'); return }
  if (formType.value === 'in' && !formExpiresAt.value) { showToast('Informe a data de validade', 'error'); return }
  try {
    await post('/production/', {
      product_id: formProductId.value,
      quantity: formQuantity.value,
      type: formType.value,
      notes: formNotes.value || undefined,
      expires_at: formType.value === 'in' ? formExpiresAt.value : undefined,
    })
    formProductId.value = 0
    formQuantity.value = 1
    formNotes.value = ''
    formExpiresAt.value = ''
    showForm.value = false
    await fetchBalance()
    showToast(formType.value === 'in' ? 'Produção registrada' : 'Saída registrada')
  } catch {
    showToast('Erro ao salvar movimento', 'error')
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
      <div>
        <p class="text-sm font-semibold text-gray-600 mb-2">Saldo Atual</p>
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b text-left">
              <th class="py-2">Produto</th>
              <th class="py-2 text-right">Qtd</th>
              <th v-if="isAdmin || isKitchen" class="py-2 text-right">Necessário</th>
              <th v-if="isAdmin || isKitchen" class="py-2 text-right">Diferença</th>
              <th v-if="isAdmin || isKitchen" class="py-2 text-right">Validade</th>
              <th v-if="isAdmin" class="py-2 text-center w-10"></th>
            </tr>
          </thead>
          <tbody>
            <template v-for="item in stockBalance" :key="item.product_id">
              <tr @click="toggle(item.product_id)" class="bg-gray-100 font-semibold cursor-pointer select-none">
                <td class="py-2">
                  <span class="inline-block w-4 transition-transform duration-150" :class="expanded.has(item.product_id) ? 'rotate-90' : ''">
                    <i class="mdi mdi-chevron-right"></i>
                  </span>
                  {{ item.product_name }}
                </td>
                <td class="py-2 text-right font-mono" :class="item.balance < 0 ? 'text-red-600' : 'text-green-700'">{{ item.balance }} {{ unitLabel(item.unit) }}</td>
                <td v-if="isAdmin || isKitchen" class="py-2 text-right font-mono">{{ neededByOrders[item.product_id] || 0 }} {{ unitLabel(item.unit) }}</td>
                <td v-if="isAdmin || isKitchen" class="py-2 text-right font-mono" :class="(item.balance - (neededByOrders[item.product_id] || 0)) < 0 ? 'text-red-600 font-bold' : 'text-green-700'">{{ (item.balance - (neededByOrders[item.product_id] || 0)).toFixed(0) }} {{ unitLabel(item.unit) }}</td>
                <td v-if="isAdmin || isKitchen" class="py-2"></td>
                <td v-if="isAdmin" class="py-2"></td>
              </tr>
              <template v-if="expanded.has(item.product_id)">
                <tr v-for="batch in item.batches" :key="batch.date" class="border-b hover:bg-gray-50 text-sm">
                  <td class="pl-6 text-gray-500">↳ {{ fmtDate(batch.created_at) }} → {{ fmtDate(batch.date) }} (lote #{{ batch.lot_ids.join(', lote #') }})</td>
                  <td class="py-1 text-right font-mono">{{ batch.quantity }} {{ unitLabel(item.unit) }}</td>
                  <td v-if="isAdmin || isKitchen" colspan="2"></td>
                  <td v-if="isAdmin || isKitchen" class="py-1 text-right font-mono text-xs" :class="expiryClass(batch.expires_at)">{{ fmtDate(batch.expires_at) }}</td>
                  <td v-if="isAdmin" class="py-1 text-center">
                    <button @click="startEdit(batch)" class="text-gray-400 hover:text-blue-600" title="Editar validade"><i class="mdi mdi-pencil"></i></button>
                  </td>
                </tr>
              </template>
            </template>
          </tbody>
        </table>
      </div>

      <o-modal v-model:active="showEditModal" :width="400" @update:active="(v: boolean) => { if (!v) editingBatch = null }">
        <div class="p-4 space-y-4">
          <p class="font-semibold">Editar Validade</p>
          <p class="text-sm text-gray-600" v-if="editingBatch">
            {{ fmtDate(editingBatch.date) }} — lote #{{ editingBatch.lot_ids.join(', lote #') }}
          </p>
          <o-field label="Nova data de validade">
            <o-input v-model="editExpiresAt" type="date" required />
          </o-field>
          <div class="flex justify-end gap-2">
            <button @click="showEditModal = false" class="px-4 py-1.5 text-sm rounded border hover:bg-gray-100">Cancelar</button>
            <button @click="saveExpiresAt" class="px-4 py-1.5 text-sm rounded bg-blue-600 text-white hover:bg-blue-700">Salvar</button>
          </div>
        </div>
      </o-modal>

      <form v-if="showForm && canWrite" @submit.prevent="submitMovement" class="border rounded-lg p-4 space-y-3 bg-gray-50">
        <p class="text-sm font-semibold text-gray-600">Movimentar Estoque</p>
        <div class="flex gap-4">
          <o-field label="Produto" class="flex-1">
            <select v-model="formProductId" class="w-full border rounded px-3 py-2 text-sm bg-white" required>
              <option :value="0" disabled>Selecione</option>
              <option v-for="p in productOptions" :key="p.value" :value="p.value">{{ p.label }}</option>
            </select>
          </o-field>
          <o-field v-if="isAdmin" label="Tipo" class="w-32">
            <select v-model="formType" class="w-full border rounded px-3 py-2 text-sm bg-white">
              <option value="in">Entrada</option>
              <option value="out">Saída</option>
            </select>
          </o-field>
          <o-field v-else label="Tipo" class="w-32">
            <div class="w-full border rounded px-3 py-2 text-sm bg-gray-100 text-gray-500">Entrada</div>
          </o-field>
          <o-field label="Qtd" class="w-32">
            <o-input v-model="formQuantity" type="number" min="1" required />
          </o-field>
        </div>
        <o-field v-if="formType === 'in'" label="Validade" variant="danger" :message="!formExpiresAt && formType === 'in' ? 'Obrigatório' : ''">
          <o-input v-model="formExpiresAt" type="date" required />
        </o-field>
        <o-field :label="formType === 'out' ? 'Motivo' : 'Observações'">
          <o-input v-model="formNotes" type="textarea" :placeholder="formType === 'out' ? 'Ex: inventário, compra, quebra...' : ''" />
        </o-field>
        <button type="submit" class="bg-green-600 hover:bg-green-700 text-white text-sm font-semibold py-1.5 px-4 rounded">{{ formType === 'in' ? 'Registrar Entrada' : 'Registrar Saída' }}</button>
      </form>

      <div v-if="canWrite" class="flex justify-center pt-2 border-t">
        <button
          type="button"
          :title="showForm ? 'Fechar' : 'Movimentar Estoque'"
          class="p-2 rounded-full hover:bg-gray-200"
          :class="showForm ? 'text-green-600 bg-green-100' : 'text-gray-600'"
          @click="showForm = !showForm"
        ><i class="mdi mdi-arrow-up-bold-circle text-2xl"></i></button>
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
