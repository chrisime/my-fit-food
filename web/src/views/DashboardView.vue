<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { get } from '@/composables/api'

const stats = ref({
  orders_today: 0,
  pending_payments: 0,
  delivered_today: 0,
  products_active: 0,
  low_stock: [] as { id: number; name: string; balance: number; unit: string }[],
  recent_orders: [] as { id: number; customer_name: string; payment_status: string; status: string; created_at: string }[],
})

onMounted(async () => {
  stats.value = await get('/dashboard/')
})
</script>

<template>
  <div>
    <h2 class="text-xl font-semibold mb-4">Dashboard</h2>

    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
      <div class="bg-white rounded-lg shadow p-4 border-l-4 border-blue-500">
        <p class="text-2xl font-bold">{{ stats.orders_today }}</p>
        <p class="text-sm text-gray-500">Pedidos hoje</p>
      </div>
      <div class="bg-white rounded-lg shadow p-4 border-l-4 border-yellow-500">
        <p class="text-2xl font-bold">{{ stats.pending_payments }}</p>
        <p class="text-sm text-gray-500">Pendentes pagamento</p>
      </div>
      <div class="bg-white rounded-lg shadow p-4 border-l-4 border-green-500">
        <p class="text-2xl font-bold">{{ stats.delivered_today }}</p>
        <p class="text-sm text-gray-500">Entregues hoje</p>
      </div>
      <div class="bg-white rounded-lg shadow p-4 border-l-4 border-purple-500">
        <p class="text-2xl font-bold">{{ stats.products_active }}</p>
        <p class="text-sm text-gray-500">Produtos ativos</p>
      </div>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <div>
        <h3 class="font-semibold mb-3">Últimos Pedidos</h3>
        <div class="bg-white rounded shadow">
          <div
            v-for="o in stats.recent_orders"
            :key="o.id"
            class="flex justify-between items-center p-3 border-b last:border-0 text-sm"
          >
            <span class="font-medium">#{{ o.id }} {{ o.customer_name }}</span>
            <span
              class="text-xs font-semibold px-2 py-0.5 rounded"
              :class="o.payment_status === 'paid' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'"
            >
              {{ o.payment_status === 'paid' ? 'PAGO' : 'PENDENTE' }}
            </span>
          </div>
          <p v-if="!stats.recent_orders.length" class="p-3 text-gray-400 text-sm">Nenhum pedido</p>
        </div>
      </div>

      <div>
        <h3 class="font-semibold mb-3">Estoque Baixo (&lt; 5)</h3>
        <div class="bg-white rounded shadow">
          <div
            v-for="s in stats.low_stock"
            :key="s.id"
            class="flex justify-between items-center p-3 border-b last:border-0 text-sm"
          >
            <span>{{ s.name }}</span>
            <span class="font-mono text-red-600 font-semibold">{{ s.balance }} {{ s.unit }}</span>
          </div>
          <p v-if="!stats.low_stock.length" class="p-3 text-green-600 text-sm">Todos os produtos com estoque suficiente</p>
        </div>
      </div>
    </div>
  </div>
</template>
