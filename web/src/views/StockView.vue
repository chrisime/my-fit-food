<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useOrderStore } from '@/stores/orders'
import { useWebSocket } from '@/composables/useWebSocket'
import { useToast } from '@/composables/useToast'
import { get, post, patch } from '@/composables/api'
import { formatQty } from '@/composables/labels'

const role = ref(localStorage.getItem('role') || '')
const isAdmin = computed(() => role.value === 'admin')
const isKitchen = computed(() => role.value === 'kitchen')
const canWrite = computed(() => isAdmin.value || isKitchen.value)

const store = useOrderStore()
const { toast, toastError } = useToast()

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

const { on, off } = useWebSocket()

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
    toast('success.expiry_updated', 'success')
    showEditModal.value = false
    editingBatch.value = null
    await fetchBalance()
  } catch (e) {
    toastError(e)
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
  try {
    await Promise.all([store.fetchOrders(), fetchBalance(), loadProducts()])
  } catch (e) {
    toastError(e)
  }
  on('stock_updated', () => {
    store.fetchOrders()
    fetchBalance()
  })
})

onUnmounted(() => {
  off('stock_updated')
})

async function loadProducts() {
  const products = await get<any[]>('/products/')
  productOptions.value = products.map((p: any) => ({ label: p.name, value: p.id }))
}

async function fetchBalance() {
  stockBalance.value = await get('/stock/balance')
}

async function submitMovement() {
  if (!formProductId.value) { toast('validation.select_product', 'warning'); return }
  if (formType.value === 'in' && !formExpiresAt.value) { toast('validation.expiry_required', 'warning'); return }
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
    toast(formType.value === 'in' ? 'success.production_registered' : 'success.exit_registered', 'success')
  } catch (e) {
    toastError(e)
  }
}
</script>

<template>
  <div>
    <div class="flex justify-between items-center mb-4">
      <h2 class="text-xl font-semibold">{{ $t('page.stock.title') }}</h2>
    </div>

    <div class="space-y-6">
      <div>
        <p class="text-sm font-semibold text-gray-600 mb-2">{{ $t('page.stock.current_balance') }}</p>
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b text-left">
              <th class="py-2">{{ $t('page.stock.product') }}</th>
              <th class="py-2 text-right">{{ $t('page.stock.qty') }}</th>
              <th v-if="isAdmin || isKitchen" class="py-2 text-right">{{ $t('page.stock.needed') }}</th>
              <th v-if="isAdmin || isKitchen" class="py-2 text-right">{{ $t('page.stock.difference') }}</th>
              <th v-if="isAdmin || isKitchen" class="py-2 text-right">{{ $t('page.stock.expiry') }}</th>
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
                <td class="py-2 text-right font-mono" :class="item.balance < 0 ? 'text-red-600' : 'text-green-700'">{{ formatQty(item.balance, item.unit) }} {{ $t('unit.' + item.unit) }}</td>
                <td v-if="isAdmin || isKitchen" class="py-2 text-right font-mono">{{ neededByOrders[item.product_id] || 0 }} {{ $t('unit.' + item.unit) }}</td>
                <td v-if="isAdmin || isKitchen" class="py-2 text-right font-mono" :class="(item.balance - (neededByOrders[item.product_id] || 0)) < 0 ? 'text-red-600 font-bold' : 'text-green-700'">{{ formatQty(item.balance - (neededByOrders[item.product_id] || 0), item.unit) }} {{ $t('unit.' + item.unit) }}</td>
                <td v-if="isAdmin || isKitchen" class="py-2"></td>
                <td v-if="isAdmin" class="py-2"></td>
              </tr>
              <template v-if="expanded.has(item.product_id)">
                <tr v-for="batch in item.batches" :key="batch.date" class="border-b hover:bg-gray-50 text-sm">
                  <td class="pl-6 text-gray-500">↳ {{ $t('page.stock.batch_info', { date: fmtDate(batch.created_at), ids: batch.lot_ids.join(', ') }) }}</td>
                  <td class="py-1 text-right font-mono">{{ formatQty(batch.quantity, item.unit) }} {{ $t('unit.' + item.unit) }}</td>
                  <td v-if="isAdmin || isKitchen" colspan="2"></td>
                  <td v-if="isAdmin || isKitchen" class="py-1 text-right font-mono text-xs" :class="expiryClass(batch.expires_at)">{{ fmtDate(batch.expires_at) }}</td>
                  <td v-if="isAdmin" class="py-1 text-center">
                    <button @click="startEdit(batch)" class="text-gray-400 hover:text-blue-600" :title="$t('page.stock.edit_expiry_title')"><i class="mdi mdi-pencil"></i></button>
                  </td>
                </tr>
              </template>
            </template>
          </tbody>
        </table>
      </div>

      <o-modal v-model:active="showEditModal" :width="400" @update:active="(v: boolean) => { if (!v) editingBatch = null }">
        <div class="p-4 space-y-4">
          <p class="font-semibold">{{ $t('page.stock.edit_expiry_modal') }}</p>
          <p class="text-sm text-gray-600" v-if="editingBatch">
            {{ $t('page.stock.batch_info', { date: fmtDate(editingBatch.date), ids: editingBatch.lot_ids.join(', ') }) }}
          </p>
          <o-field :label="$t('page.stock.new_expiry_date')">
            <o-input v-model="editExpiresAt" type="date" required />
          </o-field>
          <div class="flex justify-end gap-2">
            <button @click="showEditModal = false" class="px-4 py-1.5 text-sm rounded border hover:bg-gray-100">{{ $t('page.stock.cancel') }}</button>
            <button @click="saveExpiresAt" class="px-4 py-1.5 text-sm rounded bg-blue-600 text-white hover:bg-blue-700">{{ $t('page.stock.save') }}</button>
          </div>
        </div>
      </o-modal>

      <form v-if="showForm && canWrite" @submit.prevent="submitMovement" class="border rounded-lg p-4 space-y-3 bg-gray-50">
        <p class="text-sm font-semibold text-gray-600">{{ $t('page.stock.movement_form') }}</p>
        <div class="flex gap-4">
          <o-field :label="$t('page.stock.product_label')" class="flex-1">
            <select v-model="formProductId" class="w-full border rounded px-3 py-2 text-sm bg-white" required>
              <option :value="0" disabled>{{ $t('page.stock.select') }}</option>
              <option v-for="p in productOptions" :key="p.value" :value="p.value">{{ p.label }}</option>
            </select>
          </o-field>
          <o-field v-if="isAdmin" :label="$t('page.stock.type')" class="w-32">
            <select v-model="formType" class="w-full border rounded px-3 py-2 text-sm bg-white">
              <option value="in">{{ $t('page.stock.inbound') }}</option>
              <option value="out">{{ $t('page.stock.outbound') }}</option>
            </select>
          </o-field>
          <o-field v-else :label="$t('page.stock.type')" class="w-32">
            <div class="w-full border rounded px-3 py-2 text-sm bg-gray-100 text-gray-500">{{ $t('page.stock.inbound') }}</div>
          </o-field>
          <o-field :label="$t('page.stock.qty_label')" class="w-32">
            <o-input v-model="formQuantity" type="number" min="1" required />
          </o-field>
        </div>
        <o-field v-if="formType === 'in'" :label="$t('page.stock.expiry_label')" variant="danger" :message="!formExpiresAt && formType === 'in' ? $t('page.stock.required') : ''">
          <o-input v-model="formExpiresAt" type="date" required />
        </o-field>
        <o-field :label="formType === 'out' ? $t('page.stock.reason') : $t('page.stock.notes_label')">
          <o-input v-model="formNotes" type="textarea" :placeholder="formType === 'out' ? $t('page.stock.placeholder_out') : ''" />
        </o-field>
        <button type="submit" class="bg-green-600 hover:bg-green-700 text-white text-sm font-semibold py-1.5 px-4 rounded">{{ formType === 'in' ? $t('page.stock.register_inbound') : $t('page.stock.register_outbound') }}</button>
      </form>

      <div v-if="canWrite" class="flex justify-center pt-2 border-t">
        <button
          type="button"
          :title="showForm ? $t('page.stock.close_title') : $t('page.stock.open_title')"
          class="p-2 rounded-full hover:bg-gray-200"
          :class="showForm ? 'text-green-600 bg-green-100' : 'text-gray-600'"
          @click="showForm = !showForm"
        ><i class="mdi mdi-arrow-up-bold-circle text-2xl"></i></button>
      </div>
    </div>
  </div>
</template>
