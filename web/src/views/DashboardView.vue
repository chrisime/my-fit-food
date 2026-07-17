<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useToast } from '@/composables/useToast'
import { get } from '@/composables/api'
import { formatQty } from '@/composables/labels'

const { toastError } = useToast()

interface StockItem {
  product_id: number
  product_name: string
  balance: number
  unit: string
}

interface RecentOrder {
  id: number
  customer_name: string
  payment_status: string
  status: string
  created_at: string
  items: { quantity: number; unit_price: number; is_free: boolean }[]
}

const stats = ref({
  orders_today: 0,
  pending_payments: 0,
  delivered_today: 0,
  products_active: 0,
  low_stock: [] as { id: number; name: string; balance: number; unit: string }[],
  recent_orders: [] as RecentOrder[],
})

const allStock = ref<StockItem[]>([])
const nameFilter = ref('')
const stockFilter = ref<number | null>(7)
const orderNameFilter = ref('')
const orderDateFrom = ref('')
const orderDateTo = ref('')
const maxOrders = ref(10)

const filteredStock = computed(() => {
  return allStock.value.filter((s) => {
    const nameMatch = s.product_name.toLowerCase().includes(nameFilter.value.toLowerCase())
    if (!nameMatch) return false
    if (stockFilter.value === null) return true
    return s.balance < stockFilter.value
  })
})

const filteredOrders = computed(() => {
  const filtered = stats.value.recent_orders.filter((o) => {
    const nameMatch = o.customer_name.toLowerCase().includes(orderNameFilter.value.toLowerCase())
    if (!nameMatch) return false
    const d = o.created_at.slice(0, 10)
    if (orderDateFrom.value && d < orderDateFrom.value) return false
    if (orderDateTo.value && d > orderDateTo.value) return false
    return true
  })
  const count = maxOrders.value > 0 ? maxOrders.value : stats.value.recent_orders.length
  return filtered.slice(-count).reverse()
})

function orderTotal(o: RecentOrder): string {
  return o.items
    .filter((i) => !i.is_free)
    .reduce((sum, i) => sum + i.quantity * i.unit_price, 0)
    .toFixed(2)
}

function fmtDate(dt: string): string {
  return new Date(dt).toLocaleDateString()
}

onMounted(async () => {
  try {
    const [dashboardData, stockData, ordersData] = await Promise.all([
      get<typeof stats.value>('/dashboard/'),
      get<StockItem[]>('/stock/balance'),
      get<any[]>('/orders/'),
    ])
    stats.value = dashboardData
    stats.value.recent_orders = ordersData.map((o: any) => ({
      id: o.id,
      customer_name: o.customer_name,
      payment_status: o.payment_status,
      status: o.status,
      created_at: o.created_at,
      items: o.items || [],
    }))
    allStock.value = stockData
  } catch (e) {
    toastError(e)
  }
})
</script>

<template>
  <div>
    <h2 class="text-xl font-semibold mb-4">{{ $t('page.dashboard.title') }}</h2>

    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
      <div class="bg-white rounded-lg shadow p-4 border-l-4 border-blue-500">
        <p class="text-2xl font-bold">{{ stats.orders_today }}</p>
        <p class="text-sm text-gray-500">{{ $t('page.dashboard.orders_today') }}</p>
      </div>
      <div class="bg-white rounded-lg shadow p-4 border-l-4 border-yellow-500">
        <p class="text-2xl font-bold">{{ stats.pending_payments }}</p>
        <p class="text-sm text-gray-500">{{ $t('page.dashboard.pending_payments') }}</p>
      </div>
      <div class="bg-white rounded-lg shadow p-4 border-l-4 border-green-500">
        <p class="text-2xl font-bold">{{ stats.delivered_today }}</p>
        <p class="text-sm text-gray-500">{{ $t('page.dashboard.delivered_today') }}</p>
      </div>
      <div class="bg-white rounded-lg shadow p-4 border-l-4 border-purple-500">
        <p class="text-2xl font-bold">{{ stats.products_active }}</p>
        <p class="text-sm text-gray-500">{{ $t('page.dashboard.active_products') }}</p>
      </div>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <div>
        <h3 class="font-semibold mb-3">{{ $t('page.dashboard.recent_orders') }}</h3>
        <div class="bg-white rounded shadow">
          <div
            v-for="o in filteredOrders"
            :key="o.id"
            class="p-3 border-b last:border-0 text-sm"
          >
            <div class="flex justify-between items-center">
              <span class="font-medium">{{ o.customer_name }}</span>
              <span
                class="text-xs font-semibold px-2 py-0.5 rounded"
                :class="o.payment_status === 'paid' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'"
              >
                {{ o.payment_status === 'paid' ? $t('page.dashboard.paid') : $t('page.dashboard.pending') }}
              </span>
            </div>
            <div class="flex justify-between items-center mt-1 text-xs text-gray-400">
              <span>{{ fmtDate(o.created_at) }}</span>
              <span>R$ {{ orderTotal(o) }}</span>
            </div>
          </div>
          <p v-if="!filteredOrders.length" class="p-3 text-gray-400 text-sm">{{ $t('page.dashboard.no_orders') }}</p>
          <div class="flex flex-wrap gap-x-1 gap-y-1 p-2 border-t border-gray-100 items-center">
            <o-input v-model="orderNameFilter" class="min-w-[120px] flex-1" size="small" :placeholder="$t('page.dashboard.filter_name_placeholder')" />
            <span class="text-xs text-gray-500 ml-1">{{ $t('page.dashboard.filter_date_from') }}</span>
            <o-input v-model="orderDateFrom" type="date" class="w-28" size="small" />
            <span class="text-xs text-gray-500 ml-1">{{ $t('page.dashboard.filter_date_to') }}</span>
            <o-input v-model="orderDateTo" type="date" class="w-28" size="small" />
            <div class="flex items-center gap-1 ml-auto">
              <o-input v-model.number="maxOrders" type="number" class="w-16" size="small" min="0" placeholder="Anz." />
              <span class="text-xs text-gray-400 whitespace-nowrap">{{ filteredOrders.length }} / {{ stats.recent_orders.length }}</span>
            </div>
          </div>
        </div>
      </div>

      <div>
        <h3 class="font-semibold mb-3">{{ $t('page.dashboard.low_stock') }}</h3>
        <div class="bg-white rounded shadow">
          <div
            v-for="s in filteredStock"
            :key="s.product_id"
            class="flex justify-between items-center p-3 border-b last:border-0 text-sm"
          >
            <span>{{ s.product_name }}</span>
            <span class="font-mono font-semibold" :class="s.balance <= 0 ? 'text-red-600' : s.balance < 5 ? 'text-yellow-600' : 'text-green-700'">{{ formatQty(s.balance, s.unit) }} {{ $t('unit.' + s.unit) }}</span>
          </div>
          <p v-if="!filteredStock.length" class="p-3 text-gray-400 text-sm">{{ $t('page.dashboard.no_orders') }}</p>
          <div class="flex gap-2 p-3 border-t border-gray-100 items-center">
            <o-input v-model="nameFilter" class="w-40" size="small" :placeholder="$t('page.dashboard.filter_name_placeholder')" />
            <span class="ml-auto flex items-center gap-2">
              <o-input v-model.number="stockFilter" type="number" class="w-16" size="small" min="0" :placeholder="$t('page.dashboard.filter_stock_placeholder')" />
              <span class="text-xs text-gray-400 whitespace-nowrap">{{ filteredStock.length }} / {{ allStock.length }}</span>
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
