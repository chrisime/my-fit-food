<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useOrderStore } from '@/stores/orders'
import { useAuthStore } from '@/stores/auth'
import { useWebSocket } from '@/composables/useWebSocket'

const store = useOrderStore()
const auth = useAuthStore()
const { on, off } = useWebSocket()

const showForm = ref(false)
const customerOptions = ref<{ label: string; value: number }[]>([])
const selectedCustomerId = ref(0)
const customerData = ref<any>(null)
const selectedAddress = ref<'1' | '2'>('1')
const customerName = ref('')
const customerPhone = ref('')
const addressStreet = ref('')
const addressNeighborhood = ref('')
const addressCity = ref('')
const notes = ref('')
const items = ref([{ product_id: 0, quantity: 1, is_free: false }])
const productOptions = ref<{ label: string; value: number }[]>([])
const productPriceMap = ref<Record<number, number>>({})
const toast = ref<{ show: boolean; message: string }>({ show: false, message: '' })
let toastTimer: ReturnType<typeof setTimeout> | null = null
const search = ref('')
const showProductForm = ref(false)
const productForm = ref({ name: '', price: 0, description: '', category: '', unit: 'un', is_active: true })
const editingProductId = ref<number | null>(null)

onMounted(async () => {
  await store.fetchOrders()
  await loadProducts()
  await loadCustomers()
  on('stock_updated', () => {
    store.fetchOrders()
    showToast('Estoque atualizado pela cozinha!')
  })
})

onUnmounted(() => {
  off('stock_updated')
  if (toastTimer) clearTimeout(toastTimer)
})

function showToast(message: string) {
  toast.value = { show: true, message }
  if (toastTimer) clearTimeout(toastTimer)
  toastTimer = setTimeout(() => {
    toast.value.show = false
  }, 4000)
}

async function loadProducts() {
  const res = await fetch('/api/products/', {
    headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
  })
  if (res.ok) {
    const products = await res.json()
    productOptions.value = products.map((p: any) => ({ label: p.name, value: p.id }))
    productPriceMap.value = Object.fromEntries(products.map((p: any) => [p.id, p.price]))
  }
}

async function loadCustomers() {
  const res = await fetch('/api/customers/', {
    headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
  })
  if (res.ok) {
    const customers = await res.json()
    customerOptions.value = customers.map((c: any) => ({ label: c.name, value: c.id }))
  }
}

function selectCustomer() {
  const id = selectedCustomerId.value
  if (!id) return
  fetch(`/api/customers/${id}`, {
    headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
  })
    .then((r) => r.json())
    .then((c) => {
      customerData.value = c
      customerName.value = c.name
      customerPhone.value = c.phone || ''
      selectedAddress.value = '1'
      applyAddress('1')
    })
}

function applyAddress(which: '1' | '2') {
  selectedAddress.value = which
  const c = customerData.value
  if (!c) return
  const prefix = which === '1' ? '' : '2'
  addressStreet.value = c[`address${prefix}_street`] || ''
  addressNeighborhood.value = c[`address${prefix}_neighborhood`] || ''
  addressCity.value = c[`address${prefix}_city`] || ''
}

function openNewProduct() {
  editingProductId.value = null
  productForm.value = { name: '', price: 0, description: '', category: '', unit: 'un', is_active: true }
  showProductForm.value = true
}

function openEditProduct(productId: number) {
  const p = productOptions.value.find((x) => x.value === productId)
  if (!p) return
  editingProductId.value = productId
  productForm.value = { name: p.label, price: 0, description: '', category: '', unit: 'un', is_active: true }
  showProductForm.value = true
  fetch(`/api/products/${productId}`, {
    headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
  })
    .then((r) => r.json())
    .then((p) => {
      productForm.value = {
        name: p.name,
        price: p.price,
        description: p.description || '',
        category: p.category || '',
        unit: p.unit || 'un',
        is_active: p.is_active,
      }
    })
}

async function saveProduct() {
  const f = productForm.value
  const url = editingProductId.value
    ? `/api/products/${editingProductId.value}`
    : '/api/products/'
  const res = await fetch(url, {
    method: editingProductId.value ? 'PUT' : 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${localStorage.getItem('token')}`,
    },
    body: JSON.stringify(f),
  })
  if (!res.ok) {
    showToast('Erro ao salvar produto')
    return
  }
  showProductForm.value = false
  await loadProducts()
}

function addItem() {
  const last = items.value[items.value.length - 1]
  if (!last || last.product_id === 0) return
  items.value.push({ product_id: 0, quantity: 1, is_free: false })
}

async function submitOrder() {
  try {
    await store.createOrder({
      customer_name: customerName.value,
      customer_phone: customerPhone.value,
      address_street: addressStreet.value,
      address_neighborhood: addressNeighborhood.value,
      address_city: addressCity.value,
      notes: notes.value,
      payment_status: 'pending',
      items: items.value.filter((i) => i.product_id > 0),
    })
    await store.fetchOrders()
    customerName.value = ''
    customerPhone.value = ''
    addressStreet.value = ''
    addressNeighborhood.value = ''
    addressCity.value = ''
    notes.value = ''
    items.value = [{ product_id: 0, quantity: 1, is_free: false }]
    customerData.value = null
    selectedAddress.value = '1'
    showForm.value = false
  } catch {
    showToast('Erro ao salvar pedido. Verifique se o backend está rodando.')
  }
}

async function confirmPayment(orderId: number) {
  await store.updatePayment(orderId, 'paid')
}

function cardClass(order: any) {
  if (order.payment_status === 'paid') return 'border-green-500 bg-green-50'
  return 'border-red-300 bg-red-50'
}

const filteredOrders = computed(() => {
  if (!search.value) return store.orders
  const q = search.value.toLowerCase()
  return store.orders.filter((o) => o.customer_name.toLowerCase().includes(q))
})

const totalAmount = computed(() =>
  items.value.reduce((sum, item) => {
    if (item.is_free) return sum
    const price = productPriceMap.value[item.product_id] || 0
    return sum + price * item.quantity
  }, 0)
)

const showEditForm = ref(false)
const editingOrder = ref<any>(null)
const editItems = ref<{ product_id: number; quantity: number; is_free: boolean }[]>([])
const editNotes = ref('')

function openEditOrder(order: any) {
  editingOrder.value = order
  editNotes.value = order.notes || ''
  editItems.value = order.items.map((i: any) => ({ product_id: i.product_id, quantity: i.quantity, is_free: i.is_free }))
  showEditForm.value = true
}

async function submitEditOrder() {
  if (!editingOrder.value) return
  try {
    await store.updateOrder(editingOrder.value.id, {
      notes: editNotes.value,
      items: editItems.value.filter((i) => i.product_id > 0),
    })
    showEditForm.value = false
    showToast('Pedido atualizado')
  } catch {
    showToast('Erro ao atualizar pedido')
  }
}

async function deleteOrder(order: any) {
  if (!confirm(`Excluir pedido de "${order.customer_name}"?`)) return
  try {
    await store.deleteOrder(order.id)
    showToast('Pedido excluído')
  } catch {
    showToast('Erro ao excluir pedido')
  }
}

const editTotalAmount = computed(() =>
  editItems.value.reduce((sum, item) => {
    if ((item as any).is_free) return sum
    const price = productPriceMap.value[item.product_id] || 0
    return sum + price * item.quantity
  }, 0)
)
</script>

<template>
  <div>
    <div class="flex justify-between items-center mb-4">
      <h2 class="text-xl font-semibold">Pedidos</h2>
      <div class="flex gap-2 items-center">
        <input v-model="search" placeholder="Buscar cliente..." class="border rounded px-3 py-1.5 text-sm" />
        <button class="bg-green-600 hover:bg-green-700 text-white font-semibold py-2 px-4 rounded text-sm" @click="showForm = true">
          Novo Pedido
        </button>
      </div>
    </div>

    <o-modal v-model:active="showForm" :width="700" :content-class="'w-full'">
      <div class="rounded-lg overflow-hidden">
        <div class="bg-green-700 text-white px-6 py-4 flex items-center justify-between">
          <h3 class="text-lg font-bold">Novo Pedido</h3>
          <button class="text-white/80 hover:text-white text-xl leading-none" @click="showForm = false">&times;</button>
        </div>
        <form @submit.prevent="submitOrder" class="p-6 space-y-4">
          <o-field label="Cliente existente">
            <div class="flex gap-1">
              <select v-model="selectedCustomerId" class="flex-1 border rounded px-3 py-2 text-sm bg-white" @change="selectCustomer">
                <option :value="0">Selecione um cliente...</option>
                <option v-for="c in customerOptions" :key="c.value" :value="c.value">{{ c.label }}</option>
              </select>
              <button type="button" title="Cadastrar novo cliente" class="text-green-700 hover:text-green-800 text-lg leading-none px-1" @click="$router.push('/clientes')">+</button>
            </div>
          </o-field>
          <div class="grid grid-cols-2 gap-4">
            <o-field label="Cliente">
              <o-input v-model="customerName" required />
            </o-field>
            <o-field label="WhatsApp">
              <o-input v-model="customerPhone" placeholder="(11) 99999-9999" />
            </o-field>
          </div>
          <div class="border rounded-lg p-3 bg-gray-50 space-y-3">
            <p class="text-sm font-semibold text-gray-600">Endereço de Entrega</p>
            <div v-if="customerData?.address2_street" class="flex gap-4 mb-3">
              <label class="flex items-center gap-1.5 text-sm cursor-pointer">
                <input type="radio" name="address" value="1" :checked="selectedAddress === '1'" @change="applyAddress('1')" class="text-green-600" />
                Endereço 1
              </label>
              <label class="flex items-center gap-1.5 text-sm cursor-pointer">
                <input type="radio" name="address" value="2" :checked="selectedAddress === '2'" @change="applyAddress('2')" class="text-green-600" />
                Endereço 2
              </label>
            </div>
            <o-field label="Rua, Número">
              <o-input v-model="addressStreet" placeholder="Av. Paulista, 1000" />
            </o-field>
            <div class="grid grid-cols-2 gap-4">
              <o-field label="Bairro">
                <o-input v-model="addressNeighborhood" placeholder="Bela Vista" />
              </o-field>
              <o-field label="Cidade">
                <o-input v-model="addressCity" placeholder="São Paulo" />
              </o-field>
            </div>
          </div>
          <o-field label="Observações">
            <o-input v-model="notes" type="textarea" />
          </o-field>
          <div class="border rounded-lg p-4 bg-gray-50 space-y-3">
            <p class="text-sm font-semibold text-gray-600">Itens do Pedido</p>
            <div v-for="(item, i) in items" :key="i" class="flex gap-3 items-end">
              <o-field label="Produto" class="flex-1">
                <div class="flex gap-1">
                  <select v-model="item.product_id" class="flex-1 border rounded px-3 py-2 text-sm bg-white">
                    <option :value="0" disabled>Selecione</option>
                    <option v-for="p in productOptions" :key="p.value" :value="p.value">
                      {{ p.label }}
                    </option>
                  </select>
                  <button type="button" title="Novo produto" class="text-green-700 hover:text-green-800 text-lg leading-none px-1" @click="openNewProduct()">+</button>
                </div>
              </o-field>
              <o-field label="Qtd" class="w-24">
                <o-input v-model="item.quantity" type="number" min="1" />
              </o-field>
              <label class="flex items-center gap-1 text-xs whitespace-nowrap mb-1" style="padding-bottom:2px">
                <input type="checkbox" v-model="item.is_free" class="w-3.5 h-3.5 rounded border-gray-300 text-green-600" />
                Grátis
              </label>
            </div>
            <button type="button" class="text-sm text-green-700 font-semibold hover:underline" @click="addItem">+ Adicionar item</button>
          </div>
          <div class="text-right text-lg font-bold text-green-700">
            Total: R$ {{ totalAmount.toFixed(2) }}
          </div>
          <div class="flex justify-end gap-3 pt-2 border-t">
            <button type="button" class="bg-gray-200 hover:bg-gray-300 text-gray-700 font-semibold py-2 px-6 rounded" @click="showForm = false">
              Cancelar
            </button>
            <button type="submit" class="bg-green-600 hover:bg-green-700 text-white font-semibold py-2 px-6 rounded shadow-sm">
              Salvar Pedido
            </button>
          </div>
        </form>
      </div>
    </o-modal>

    <o-modal v-model:active="showEditForm" :width="600">
      <div class="rounded-lg overflow-hidden">
        <div class="bg-green-700 text-white px-6 py-4 flex items-center justify-between">
          <h3 class="text-lg font-bold">Editar Pedido — {{ editingOrder?.customer_name }}</h3>
          <button class="text-white/80 hover:text-white text-xl leading-none" @click="showEditForm = false">&times;</button>
        </div>
        <form @submit.prevent="submitEditOrder" class="p-6 space-y-4">
          <o-field label="Observações">
            <o-input v-model="editNotes" type="textarea" />
          </o-field>
          <div class="border rounded-lg p-4 bg-gray-50 space-y-3">
            <p class="text-sm font-semibold text-gray-600">Itens do Pedido</p>
            <div v-for="(item, i) in editItems" :key="i" class="flex gap-3 items-end">
              <o-field label="Produto" class="flex-1">
                <select v-model="item.product_id" class="w-full border rounded px-3 py-2 text-sm bg-white">
                  <option :value="0" disabled>Selecione</option>
                  <option v-for="p in productOptions" :key="p.value" :value="p.value">{{ p.label }}</option>
                </select>
              </o-field>
              <o-field label="Qtd" class="w-24">
                <o-input v-model="item.quantity" type="number" min="1" />
              </o-field>
              <label class="flex items-center gap-1 text-xs whitespace-nowrap mb-1" style="padding-bottom:2px">
                <input type="checkbox" v-model="item.is_free" class="w-3.5 h-3.5 rounded border-gray-300 text-green-600" />
                Grátis
              </label>
            </div>
            <button type="button" class="text-sm text-green-700 font-semibold hover:underline" @click="editItems.push({ product_id: 0, quantity: 1, is_free: false })">+ Adicionar item</button>
          </div>
          <div class="text-right text-lg font-bold text-green-700">
            Total: R$ {{ editTotalAmount.toFixed(2) }}
          </div>
          <div class="flex justify-end gap-3 pt-2 border-t">
            <button type="button" class="bg-gray-200 hover:bg-gray-300 text-gray-700 font-semibold py-2 px-6 rounded" @click="showEditForm = false">Cancelar</button>
            <button type="submit" class="bg-green-600 hover:bg-green-700 text-white font-semibold py-2 px-6 rounded shadow-sm">Salvar</button>
          </div>
        </form>
      </div>
    </o-modal>

    <o-modal v-model:active="showProductForm" :width="450">
      <div class="rounded-lg overflow-hidden">
        <div class="bg-green-700 text-white px-6 py-4 flex items-center justify-between">
          <h3 class="text-lg font-bold">{{ editingProductId ? 'Editar' : 'Novo' }} Produto</h3>
          <button class="text-white/80 hover:text-white text-xl leading-none" @click="showProductForm = false">&times;</button>
        </div>
        <form @submit.prevent="saveProduct" class="p-6 space-y-4">
          <o-field label="Nome">
            <o-input v-model="productForm.name" required />
          </o-field>
          <div class="flex gap-4">
            <o-field label="Preço (R$)" class="flex-1">
              <o-input v-model="productForm.price" type="number" step="0.1" min="0" required />
            </o-field>
            <o-field label="Unidade" class="w-28">
              <select v-model="productForm.unit" class="w-full border rounded px-3 py-2 text-sm bg-white">
                <option value="un">un</option>
                <option value="porção">porção</option>
                <option value="kg">kg</option>
                <option value="L">L</option>
              </select>
            </o-field>
          </div>
          <o-field label="Categoria">
            <select v-model="productForm.category" class="w-full border rounded px-3 py-2 text-sm bg-white">
              <option value="">Sem categoria</option>
              <option value="marmita">Marmita</option>
              <option value="acompanhamento">Acompanhamento</option>
              <option value="suco">Suco</option>
              <option value="brownie">Brownie</option>
              <option value="caldo">Caldo</option>
            </select>
          </o-field>
          <o-field label="Descrição">
            <o-input v-model="productForm.description" type="textarea" />
          </o-field>
          <label class="flex items-center gap-2 cursor-pointer select-none">
            <input type="checkbox" v-model="productForm.is_active" class="w-4 h-4 rounded border-gray-300 text-green-600 focus:ring-green-500" />
            <span class="text-sm font-medium text-gray-700">Ativo</span>
          </label>
          <div class="flex justify-end gap-3 pt-2 border-t">
            <button type="button" class="bg-gray-200 hover:bg-gray-300 text-gray-700 font-semibold py-2 px-6 rounded" @click="showProductForm = false">
              Cancelar
            </button>
            <button type="submit" class="bg-green-600 hover:bg-green-700 text-white font-semibold py-2 px-6 rounded shadow-sm">
              Salvar
            </button>
          </div>
        </form>
      </div>
    </o-modal>

    <transition name="fade">
      <div
        v-if="toast.show"
        class="fixed top-4 right-4 bg-green-600 text-white px-4 py-3 rounded shadow-lg z-50 text-sm"
      >
        {{ toast.message }}
      </div>
    </transition>

    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <div
        v-for="order in filteredOrders"
        :key="order.id"
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
            <span>{{ item.quantity }}x {{ item.product_name || 'Produto #' + item.product_id }} <span v-if="item.is_free" class="text-green-600 text-xs font-semibold">(gratis)</span></span>
            <span v-if="!item.is_free">R$ {{ (item.quantity * item.unit_price).toFixed(2) }}</span>
            <span v-else class="text-green-600 font-semibold">GRÁTIS</span>
          </div>
          <div class="flex justify-between font-bold text-green-700 mt-2 pt-2 border-t border-gray-300">
            <span>Total</span>
            <span>R$ {{ order.items.reduce((s, i) => s + (i.is_free ? 0 : i.quantity * i.unit_price), 0).toFixed(2) }}</span>
          </div>
        </div>
        <p v-if="order.notes" class="mt-2 text-xs text-gray-500 italic">{{ order.notes }}</p>
        <div class="mt-auto pt-3 space-y-2">
          <div v-if="order.payment_status === 'pending'" class="flex gap-2">
            <button @click="openEditOrder(order)" class="bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold py-2 px-3 rounded" title="Editar">
              <i class="mdi mdi-pencil"></i>
            </button>
            <button @click="deleteOrder(order)" class="bg-red-600 hover:bg-red-700 text-white text-sm font-semibold py-2 px-3 rounded" title="Excluir">
              <i class="mdi mdi-delete"></i>
            </button>
            <button @click="confirmPayment(order.id)" class="flex-1 bg-green-600 hover:bg-green-700 text-white text-sm font-semibold py-2 px-3 rounded">
              Confirmar Pagamento
            </button>
          </div>
          <button
            v-if="order.payment_status === 'paid' && auth.user?.role === 'admin'"
            @click="store.reversePayment(order.id)"
            class="w-full bg-yellow-500 hover:bg-yellow-600 text-white text-sm font-semibold py-2 px-3 rounded"
          >
            Reverter Pagamento
          </button>
        </div>
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
