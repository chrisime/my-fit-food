<script setup lang="ts">
import type { Order } from '@/stores/orders'

const props = defineProps<{
  order: Order
  role: string
}>()

const emit = defineEmits<{
  edit: [order: Order]
  delete: [order: Order]
  'confirm-payment': [orderId: number]
  'reverse-payment': [orderId: number]
}>()

function cardClass(order: Order) {
  if (order.payment_status === 'paid') return 'border-green-500 bg-green-50'
  return 'border-red-300 bg-red-50'
}

function total(order: Order) {
  return order.items.reduce((s, i) => s + (i.is_free ? 0 : i.quantity * i.unit_price), 0).toFixed(2)
}
</script>

<template>
  <div
    class="border-2 rounded-lg p-4 shadow-sm flex flex-col h-full"
    :class="cardClass(order)"
  >
    <div class="flex justify-between items-start">
      <div>
        <p class="font-bold text-lg">{{ order.customer_name }}</p>
        <p v-if="order.customer_phone" class="text-sm text-gray-500">{{ order.customer_phone }}</p>
        <p v-if="order.address_street || order.address_neighborhood || order.address_city" class="text-xs text-gray-400 mt-1">
          {{ [order.address_street, order.address_neighborhood, order.address_city].filter(Boolean).join(' — ') }}
        </p>
      </div>
      <span
        class="text-xs font-bold px-2 py-1 rounded"
        :class="order.payment_status === 'paid' ? 'bg-green-200 text-green-800' : 'bg-red-200 text-red-800'"
      >
        {{ order.payment_status === 'paid' ? 'PAGO' : 'PENDENTE' }}
      </span>
    </div>
    <div class="mt-2 text-sm flex-1">
      <div v-for="item in order.items" :key="item.id" class="flex justify-between">
        <span>
          {{ item.quantity }}x {{ item.product_name || 'Produto #' + item.product_id }}
          <span v-if="item.is_free" class="text-green-600 text-xs font-semibold">(gratis)</span>
        </span>
        <span v-if="!item.is_free">R$ {{ (item.quantity * item.unit_price).toFixed(2) }}</span>
        <span v-else class="text-green-600 font-semibold">GRÁTIS</span>
      </div>
      <div class="flex justify-between font-bold text-green-700 mt-2 pt-2 border-t border-gray-300">
        <span>Total</span>
        <span>R$ {{ total(order) }}</span>
      </div>
    </div>
    <p v-if="order.notes" class="mt-2 text-xs text-gray-500 italic">{{ order.notes }}</p>
    <div class="mt-auto pt-3 space-y-2">
      <div v-if="order.payment_status === 'pending'" class="flex gap-2">
        <button @click="emit('edit', order)" class="bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold py-2 px-3 rounded" title="Editar">
          <i class="mdi mdi-pencil"></i>
        </button>
        <button @click="emit('delete', order)" class="bg-red-600 hover:bg-red-700 text-white text-sm font-semibold py-2 px-3 rounded" title="Excluir">
          <i class="mdi mdi-delete"></i>
        </button>
        <button @click="emit('confirm-payment', order.id)" class="flex-1 bg-green-600 hover:bg-green-700 text-white text-sm font-semibold py-2 px-3 rounded">
          Confirmar Pagamento
        </button>
      </div>
      <button
        v-if="order.payment_status === 'paid' && role === 'admin'"
        @click="emit('reverse-payment', order.id)"
        class="w-full bg-yellow-500 hover:bg-yellow-600 text-white text-sm font-semibold py-2 px-3 rounded"
      >
        Reverter Pagamento
      </button>
    </div>
  </div>
</template>
