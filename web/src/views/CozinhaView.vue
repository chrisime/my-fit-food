<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useOrderStore } from '@/stores/orders'
import { useWebSocket } from '@/composables/useWebSocket'
import { get, post } from '@/composables/api'

const store = useOrderStore()
const { on, off } = useWebSocket()

const showStockModal = ref(false)
const stockBalance = ref<{ product_id: number; product_name: string; balance: number; unit: string }[]>([])
const productOptions = ref<{ label: string; value: number }[]>([])
const currentRole = ref(localStorage.getItem('role') || '')
const showProdForm = ref(false)
const prodProductId = ref(0)
const toast = ref<{ show: boolean; message: string; type: 'success' | 'error' }>({ show: false, message: '', type: 'success' })
let toastTimer: ReturnType<typeof setTimeout> | null = null

function showToast(message: string, type: 'success' | 'error' = 'success') {
  toast.value = { show: true, message, type }
  if (toastTimer) clearTimeout(toastTimer)
  toastTimer = setTimeout(() => { toast.value.show = false }, 4000)
}
const prodQuantity = ref(1)
const prodNotes = ref('')
const showAdjustForm = ref(false)
const adjustProductId = ref(0)
const adjustType = ref<'in' | 'out'>('in')
const adjustQuantity = ref(1)
const adjustNotes = ref('')

onMounted(async () => {
  await Promise.all([store.fetchOrders(), loadProducts(), fetchBalance()])
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

function quickProduce(productId: number) {
  prodProductId.value = productId
  prodQuantity.value = 1
  prodNotes.value = ''
  showStockModal.value = true
  showProdForm.value = true
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
</script>

<template>
  <div>
    <div class="flex justify-between items-center mb-4">
      <h2 class="text-xl font-semibold">Cozinha</h2>
      <button class="bg-gray-200 hover:bg-gray-300 text-gray-700 font-semibold py-2 px-3 rounded text-sm" @click="showStockModal = true">Estoque</button>
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

  <o-modal v-model:active="showStockModal" :width="1600">
      <div class="rounded-lg overflow-hidden w-full">
        <div class="bg-green-700 text-white px-6 py-4 flex items-center justify-between">
          <h3 class="text-lg font-bold">Estoque</h3>
          <button class="text-white/80 hover:text-white text-xl leading-none" @click="showStockModal = false">&times;</button>
        </div>
        <div class="p-6 space-y-6 w-full">
          <form v-if="showProdForm" @submit.prevent="submitProduction" class="border rounded-lg p-4 space-y-3 bg-gray-50 w-full">
            <p class="text-sm font-semibold text-gray-600">Registrar Produção</p>
            <div class="flex gap-4 w-full">
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

          <form v-if="showAdjustForm" @submit.prevent="submitAdjust" class="border rounded-lg p-4 space-y-3 bg-gray-50 w-full">
            <p class="text-sm font-semibold text-gray-600">Ajuste de Estoque</p>
            <div class="flex gap-4 w-full">
              <o-field label="Produto" class="flex-1">
                <select v-model="adjustProductId" class="w-full border rounded px-3 py-2 text-sm bg-white" required>
                  <option :value="0" disabled>Selecione</option>
                  <option v-for="p in productOptions" :key="p.value" :value="p.value">{{ p.label }}</option>
                </select>
              </o-field>
              <o-field v-if="currentRole === 'admin'" label="Tipo" class="w-32">
                <select v-model="adjustType" class="w-full border rounded px-3 py-2 text-sm bg-white">
                  <option value="in">Entrada</option>
                  <option value="out">Saída</option>
                </select>
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

          <div class="w-full">
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
                  <td class="py-2 text-right font-mono">{{ neededByOrders[item.product_id] || 0 }} {{ item.unit }}</td>
                  <td class="py-2 text-right font-mono" :class="(item.balance - (neededByOrders[item.product_id] || 0)) < 0 ? 'text-red-600 font-bold' : 'text-green-700'">{{ (item.balance - (neededByOrders[item.product_id] || 0)).toFixed(0) }} {{ item.unit }}</td>
                </tr>
              </tbody>
            </table>
          </div>

          <div class="flex justify-center gap-4 pt-2 border-t">
            <button
              type="button"
              :title="showProdForm ? 'Fechar produção' : 'Produzir'"
              class="p-2 rounded-full hover:bg-gray-200"
              :class="showProdForm ? 'text-green-600 bg-green-100' : 'text-gray-600'"
              @click="showProdForm = !showProdForm"
            ><i class="mdi mdi-plus-circle text-2xl"></i></button>
            <button
              v-if="currentRole === 'admin'"
              type="button"
              :title="showAdjustForm ? 'Fechar ajuste' : 'Ajustar'"
              class="p-2 rounded-full hover:bg-gray-200"
              :class="showAdjustForm ? 'text-green-600 bg-green-100' : 'text-gray-600'"
              @click="showAdjustForm = !showAdjustForm"
            ><i class="mdi mdi-tune text-2xl"></i></button>
          </div>
        </div>
      </div>
    </o-modal>

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
                class="text-xs font-semibold px-2 py-0.5 rounded whitespace-nowrap cursor-pointer"
                :class="needsProduction(item.product_id, item.quantity) ? 'bg-yellow-100 text-yellow-800 hover:bg-yellow-200' : 'bg-green-100 text-green-800'"
                @click="needsProduction(item.product_id, item.quantity) && quickProduce(item.product_id)"
                :title="needsProduction(item.product_id, item.quantity) ? 'Clique para produzir' : ''"
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
