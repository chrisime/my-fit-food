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

const showForm = ref(false)
const formProductId = ref(0)
const formType = ref<'in' | 'out'>('in')
const formQuantity = ref(1)
const formNotes = ref('')
const formExpiresAt = ref<Date | undefined>(undefined)
const formProductName = ref('')

function openMovement(productId: number, productName: string) {
  formProductId.value = productId
  formProductName.value = productName
  formType.value = 'in'
  formQuantity.value = 1
  formNotes.value = ''
  formExpiresAt.value = undefined
  showForm.value = true
}

function toDateStr(d: Date | undefined): string | undefined {
  if (!d) return undefined
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

function parseDate(str: string): Date {
  const [y, m, d] = str.split('-').map(Number)
  return new Date(y, m - 1, d)
}

const { on, off } = useWebSocket()

const showEditModal = ref(false)
const editingBatch = ref<Batch | null>(null)
const editExpiresAt = ref<Date | undefined>(undefined)

function startEdit(batch: Batch) {
  editingBatch.value = batch
  editExpiresAt.value = batch.expires_at ? parseDate(batch.expires_at) : undefined
  showEditModal.value = true
}

async function saveExpiresAt() {
  if (!editingBatch.value) return
  try {
    await patch('/stock/batch/expires-at', {
      movement_ids: editingBatch.value.lot_ids,
      expires_at: toDateStr(editExpiresAt.value),
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
    await Promise.all([store.fetchOrders(), fetchBalance()])
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
      expires_at: formType.value === 'in' ? toDateStr(formExpiresAt.value) : undefined,
    })
    formProductId.value = 0
    formQuantity.value = 1
    formNotes.value = ''
    formExpiresAt.value = undefined
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
              <th v-if="canWrite" class="py-2 text-center w-10"></th>
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
                <td v-if="canWrite" class="py-2 text-center">
                  <o-button variant="primary" size="small" @click.stop="openMovement(item.product_id, item.product_name)">
                    <i class="mdi mdi-plus"></i>
                  </o-button>
                </td>
              </tr>
              <template v-if="expanded.has(item.product_id)">
                <tr v-for="batch in item.batches" :key="batch.date" class="border-b hover:bg-gray-50 text-sm">
                  <td class="pl-6 text-gray-500">↳ {{ $t('page.stock.batch_info', { date: fmtDate(batch.created_at), ids: batch.lot_ids.join(', ') }) }}</td>
                  <td class="py-1 text-right font-mono">{{ formatQty(batch.quantity, item.unit) }} {{ $t('unit.' + item.unit) }}</td>
                  <td v-if="isAdmin || isKitchen" colspan="2"></td>
                  <td v-if="isAdmin || isKitchen" class="py-1 text-right font-mono text-xs" :class="expiryClass(batch.expires_at)">{{ fmtDate(batch.expires_at) }}</td>
                  <td v-if="isAdmin" class="py-1 text-center">
                    <o-button @click="startEdit(batch)" variant="info" size="small" class="text-gray-400" :title="$t('page.stock.edit_expiry_title')"><i class="mdi mdi-pencil"></i></o-button>
                  </td>
                </tr>
              </template>
            </template>
          </tbody>
        </table>
      </div>

      <o-modal v-model:active="showEditModal" :width="500" @update:active="(v: boolean) => { if (!v) editingBatch = null }">
        <div class="p-4 space-y-4">
          <p class="font-semibold">{{ $t('page.stock.edit_expiry_modal') }}</p>
          <p class="text-sm text-gray-600" v-if="editingBatch">
            {{ $t('page.stock.batch_info', { date: fmtDate(editingBatch.date), ids: editingBatch.lot_ids.join(', ') }) }}
          </p>
          <o-field :label="$t('page.stock.new_expiry_date')">
            <o-datepicker v-model="editExpiresAt" icon="calendar" teleport />
          </o-field>
          <div class="flex justify-end gap-2">
            <o-button @click="showEditModal = false">{{ $t('page.stock.cancel') }}</o-button>
            <o-button @click="saveExpiresAt" variant="info">{{ $t('page.stock.save') }}</o-button>
          </div>
        </div>
      </o-modal>

      <o-modal v-model:active="showForm" :width="450">
        <div class="rounded-lg overflow-hidden">
          <div class="bg-green-700 text-white px-6 py-4 flex items-center justify-between">
            <h3 class="text-lg font-bold">{{ $t('page.stock.movement_form') }} — {{ formProductName }}</h3>
            <o-button variant="ghost" class="text-white/80" @click="showForm = false">&times;</o-button>
          </div>
          <form @submit.prevent="submitMovement" class="p-6 space-y-4">
            <div class="flex gap-4">
              <o-field v-if="isAdmin" :label="$t('page.stock.type')" class="w-36">
                <o-select v-model="formType">
                  <option value="in">{{ $t('page.stock.inbound') }}</option>
                  <option value="out">{{ $t('page.stock.outbound') }}</option>
                </o-select>
              </o-field>
              <o-field v-else :label="$t('page.stock.type')" class="w-36">
                <div class="w-full border rounded px-4 py-2.5 text-sm bg-gray-100 text-gray-500">{{ $t('page.stock.inbound') }}</div>
              </o-field>
              <o-field :label="$t('page.stock.qty_label')" class="flex-1">
                <o-input v-model="formQuantity" type="number" min="1" required />
              </o-field>
              <o-field v-if="formType === 'in'" :label="$t('page.stock.expiry_label')" class="flex-1" variant="danger" :message="!formExpiresAt && formType === 'in' ? $t('page.stock.required') : ''">
                <o-datepicker v-model="formExpiresAt" icon="calendar" teleport />
              </o-field>
            </div>
            <o-field :label="formType === 'out' ? $t('page.stock.reason') : $t('page.stock.notes_label')">
              <o-input v-model="formNotes" type="textarea" :placeholder="formType === 'out' ? $t('page.stock.placeholder_out') : ''" />
            </o-field>
            <div class="flex justify-end gap-3 pt-2 border-t">
              <o-button type="button" @click="showForm = false">
                {{ $t('page.stock.cancel') }}
              </o-button>
              <o-button variant="primary" type="submit">
                {{ formType === 'in' ? $t('page.stock.register_inbound') : $t('page.stock.register_outbound') }}
              </o-button>
            </div>
          </form>
        </div>
      </o-modal>
    </div>
  </div>
</template>
