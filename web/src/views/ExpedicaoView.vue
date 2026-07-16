<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useOrderStore } from '@/stores/orders'
import { useAuthStore } from '@/stores/auth'
import { useToast } from '@/composables/useToast'
import { get } from '@/composables/api'

const { toastError } = useToast()

const store = useOrderStore()
const auth = useAuthStore()
const stockBalance = ref<{ product_id: number; product_name: string; balance: number; unit: string }[]>([])
const paidOrders = computed(() =>
  store.orders.filter((o) => o.payment_status === 'paid' && o.status !== 'delivered')
)
const historyOrders = computed(() =>
  store.orders.filter((o) => o.status === 'delivered')
)

async function fetchBalance() {
  try {
    stockBalance.value = await get('/stock/balance')
  } catch (e) {
    toastError(e)
  }
}

function stockFor(productId: number): number {
  const found = stockBalance.value.find((s) => s.product_id === productId)
  return found ? found.balance : 0
}

function orderHasMissingStock(order: any): boolean {
  return order.items.some((item: any) => stockFor(item.product_id) < item.quantity)
}

onMounted(async () => {
  try {
    await Promise.all([store.fetchOrders(), fetchBalance()])
  } catch (e) {
    toastError(e)
  }
})

function formatDate(dt: string) {
  return new Date(dt).toLocaleString('pt-BR')
}

async function deliverAndRefresh(orderId: number) {
  try {
    await store.deliverOrder(orderId)
    await fetchBalance()
  } catch (e) {
    toastError(e)
  }
}

async function reverseAndRefresh(orderId: number) {
  try {
    await store.reverseDelivery(orderId)
    await fetchBalance()
  } catch (e) {
    toastError(e)
  }
}
</script>

<template>
  <div>
    <div class="flex justify-between items-center mb-4">
      <h2 class="text-xl font-semibold">{{ $t('page.dispatch.title') }}</h2>
      <router-link to="/stock" class="text-sm bg-gray-200 hover:bg-gray-300 font-semibold py-1.5 px-3 rounded">{{ $t('page.dispatch.view_stock') }}</router-link>
    </div>


    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <div
        v-for="order in paidOrders"
        :key="order.id"
        class="border-2 rounded-lg p-4 shadow-sm flex flex-col h-full"
        :class="orderHasMissingStock(order) ? 'border-red-400 bg-red-50' : 'border-green-500 bg-white'"
      >
        <div class="flex justify-between items-start">
          <div>
            <p class="font-bold text-lg">{{ order.customer_name }}</p>
            <p v-if="order.customer_phone" class="text-sm text-gray-500">{{ order.customer_phone }}</p>
            <p v-if="order.address_street || order.address_neighborhood || order.address_city" class="text-xs text-gray-400 mt-1">
              {{ [order.address_street, order.address_neighborhood, order.address_city].filter(Boolean).join(' — ') }}
            </p>
            <p class="text-xs text-gray-400">{{ formatDate(order.created_at) }}</p>
          </div>
          <span class="text-xs font-bold bg-green-200 text-green-800 px-2 py-1 rounded">{{ $t('page.dispatch.paid') }}</span>
        </div>

        <div class="mt-3 text-sm space-y-1 flex-1">
          <div v-for="item in order.items" :key="item.id" class="flex justify-between items-center">
            <span>{{ item.quantity }}x {{ item.product_name || $t('page.dispatch.product_fallback') + item.product_id }}</span>
            <span
              v-if="stockFor(item.product_id) < item.quantity"
              class="text-xs px-2 py-0.5 rounded font-semibold bg-red-100 text-red-700"
            >
              {{ $t('page.dispatch.missing', { qty: item.quantity - stockFor(item.product_id) }) }}
            </span>
          </div>
        </div>

        <div class="mt-auto pt-4">
          <button
            v-if="!orderHasMissingStock(order)"
            class="w-full bg-green-600 hover:bg-green-700 text-white font-semibold text-sm py-2 px-3 rounded"
            @click="deliverAndRefresh(order.id)"
          >
            {{ $t('page.dispatch.confirm_deliver') }}
          </button>
          <p v-else class="text-red-600 text-sm font-semibold text-center">{{ $t('page.dispatch.insufficient_stock') }}</p>
        </div>
      </div>
    </div>

    <div v-if="paidOrders.length === 0" class="text-gray-400 text-center py-8">
      {{ $t('page.dispatch.no_orders') }}
    </div>

    <div v-if="historyOrders.length" class="mt-10">
      <h3 class="font-semibold text-gray-500 mb-2">{{ $t('page.dispatch.delivered_today') }}</h3>
      <div class="space-y-2">
        <div v-for="order in historyOrders" :key="order.id"
          class="bg-gray-100 rounded p-3 text-sm flex justify-between items-center">
          <span>{{ order.customer_name }}</span>
          <div class="flex items-center gap-2">
            <span class="text-gray-400">{{ formatDate(order.delivered_at || '') }}</span>
            <button
              v-if="auth.user?.role === 'admin'"
              @click="reverseAndRefresh(order.id)"
              class="text-xs bg-yellow-500 hover:bg-yellow-600 text-white font-semibold py-1 px-2 rounded"
            >
              {{ $t('page.dispatch.revert') }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
