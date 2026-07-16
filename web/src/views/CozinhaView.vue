<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useOrderStore } from '@/stores/orders'
import { useWebSocket } from '@/composables/useWebSocket'
import { useToast } from '@/composables/useToast'
import { get } from '@/composables/api'
import { formatQty } from '@/composables/labels'

const store = useOrderStore()
const { on, off } = useWebSocket()
const { toastError } = useToast()

const stockBalance = ref<{ product_id: number; product_name: string; balance: number; unit: string }[]>([])

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
  try {
    stockBalance.value = await get('/stock/balance')
  } catch (e) {
    toastError(e)
  }
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
      <h2 class="text-xl font-semibold">{{ $t('page.kitchen.title') }}</h2>
      <router-link to="/stock" class="bg-gray-200 hover:bg-gray-300 text-gray-700 font-semibold py-2 px-3 rounded text-sm">{{ $t('page.kitchen.view_stock') }}</router-link>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <div>
        <h3 class="font-semibold text-red-700 mb-2">{{ $t('page.kitchen.pending_header') }}</h3>
        <div
          v-for="order in pendingOrders"
          :key="order.id"
          class="border-2 border-red-300 bg-red-50 rounded-lg p-4 mb-3 shadow-sm"
        >
          <p class="font-bold">{{ order.customer_name }}</p>
          <p class="text-sm text-gray-500">{{ order.items.length }} {{ $t('page.kitchen.items') }}</p>
        </div>
        <p v-if="!pendingOrders.length" class="text-gray-400 text-sm">{{ $t('page.kitchen.no_pending') }}</p>
      </div>

      <div>
        <h3 class="font-semibold text-green-700 mb-2">{{ $t('page.kitchen.paid_header') }}</h3>
        <div
          v-for="order in paidOrders"
          :key="order.id"
          class="border-2 border-green-500 bg-green-50 rounded-lg p-4 mb-3 shadow-sm"
        >
          <p class="font-bold">{{ order.customer_name }}</p>
          <p v-if="order.address_street || order.address_neighborhood || order.address_city" class="text-xs text-gray-500 mt-1">
            {{ [order.address_street, order.address_neighborhood, order.address_city].filter(Boolean).join(' — ') }}
          </p>
          <p v-if="order.notes" class="text-xs text-gray-500 italic mt-1">{{ $t('page.kitchen.notes_prefix') }} {{ order.notes }}</p>
          <div class="text-sm mt-2 space-y-1">
            <div v-for="item in order.items" :key="item.id" class="flex items-center justify-between gap-2">
              <span>{{ item.quantity }}x {{ item.product_name || $t('page.kitchen.product_fallback') + item.product_id }}</span>
              <span
                class="text-xs font-semibold px-2 py-0.5 rounded whitespace-nowrap"
                :class="needsProduction(item.product_id, item.quantity) ? 'bg-yellow-100 text-yellow-800' : 'bg-green-100 text-green-800'"
              >
                <template v-if="needsProduction(item.product_id, item.quantity)">
                  {{ $t('page.kitchen.needs_production', { qty: formatQty(stockFor(item.product_id).balance, stockFor(item.product_id).unit), unit: $t('unit.' + stockFor(item.product_id).unit) }) }}
                </template>
                <template v-else>
                  {{ $t('page.kitchen.in_stock', { qty: formatQty(stockFor(item.product_id).balance, stockFor(item.product_id).unit), unit: $t('unit.' + stockFor(item.product_id).unit) }) }}
                </template>
              </span>
            </div>
          </div>
        </div>
        <p v-if="!paidOrders.length" class="text-gray-400 text-sm">{{ $t('page.kitchen.no_paid') }}</p>
      </div>
    </div>
  </div>
</template>
