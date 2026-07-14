<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useOrderStore } from '@/stores/orders'
import { useAuthStore } from '@/stores/auth'
import { useWebSocket } from '@/composables/useWebSocket'
import { get, post, put } from '@/composables/api'
import OrderCard from '@/components/orders/OrderCard.vue'
import OrderFormModal from '@/components/orders/OrderFormModal.vue'
import EditOrderModal from '@/components/orders/EditOrderModal.vue'

const store = useOrderStore()
const auth = useAuthStore()
const { on, off } = useWebSocket()

const showForm = ref(false)
const showEditForm = ref(false)
const editingOrder = ref<any>(null)
const customerOptions = ref<{ label: string; value: number }[]>([])
const productOptions = ref<{ label: string; value: number }[]>([])
const productPriceMap = ref<Record<number, number>>({})
const search = ref('')
const toast = ref<{ show: boolean; message: string }>({ show: false, message: '' })
let toastTimer: ReturnType<typeof setTimeout> | null = null

const showProductForm = ref(false)
const editingProductId = ref<number | null>(null)
const productForm = ref({ name: '', price: 0, description: '', category: '', unit: 'un', is_active: true })

onMounted(async () => {
  await Promise.all([store.fetchOrders(), loadProducts(), loadCustomers()])
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
  toastTimer = setTimeout(() => { toast.value.show = false }, 4000)
}

async function loadProducts() {
  const products = await get<any[]>('/products/')
  productOptions.value = products.map((p) => ({ label: p.name, value: p.id }))
  productPriceMap.value = Object.fromEntries(products.map((p) => [p.id, p.price]))
}

async function loadCustomers() {
  const customers = await get<any[]>('/customers/')
  customerOptions.value = customers.map((c) => ({ label: c.name, value: c.id }))
}

function openEditOrder(order: any) {
  editingOrder.value = order
  showEditForm.value = true
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

async function confirmPayment(orderId: number) {
  await store.updatePayment(orderId, 'paid')
}

function openNewProduct() {
  editingProductId.value = null
  productForm.value = { name: '', price: 0, description: '', category: '', unit: 'un', is_active: true }
  showProductForm.value = true
}

function openEditProduct(productId: number) {
  editingProductId.value = productId
  showProductForm.value = true
  get<any>(`/products/${productId}`).then((p) => {
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
  const url = editingProductId.value ? `/products/${editingProductId.value}` : '/products/'
  const method = editingProductId.value ? put : post
  try {
    await method(url, f)
    showProductForm.value = false
    await loadProducts()
  } catch {
    showToast('Erro ao salvar produto')
  }
}

const filteredOrders = computed(() => {
  if (!search.value) return store.orders
  const q = search.value.toLowerCase()
  return store.orders.filter((o) => o.customer_name.toLowerCase().includes(q))
})
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

    <OrderFormModal
      :active="showForm"
      :product-options="productOptions"
      :customer-options="customerOptions"
      :product-price-map="productPriceMap"
      @close="showForm = false"
      @new-product="openNewProduct()"
    />

    <EditOrderModal
      :active="showEditForm"
      :order="editingOrder"
      :product-options="productOptions"
      :product-price-map="productPriceMap"
      @close="showEditForm = false"
      @error="showToast"
    />

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
      <div v-if="toast.show" class="fixed top-4 right-4 bg-green-600 text-white px-4 py-3 rounded shadow-lg z-50 text-sm">
        {{ toast.message }}
      </div>
    </transition>

    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <OrderCard
        v-for="order in filteredOrders"
        :key="order.id"
        :order="order"
        :role="auth.user?.role || ''"
        @edit="openEditOrder"
        @delete="deleteOrder"
        @confirm-payment="confirmPayment"
        @reverse-payment="store.reversePayment"
      />
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
