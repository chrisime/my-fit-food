<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useOrderStore } from '@/stores/orders'
import { useAuthStore } from '@/stores/auth'
import { useWebSocket } from '@/composables/useWebSocket'
import { useToast } from '@/composables/useToast'
import { get, post, put } from '@/composables/api'
import { useI18n } from 'vue-i18n'
import OrderCard from '@/components/orders/OrderCard.vue'
import OrderFormModal from '@/components/orders/OrderFormModal.vue'
import EditOrderModal from '@/components/orders/EditOrderModal.vue'

const store = useOrderStore()
const auth = useAuthStore()
const { on, off } = useWebSocket()
const { toast, toastError } = useToast()
const { t } = useI18n()

const showForm = ref(false)
const showEditForm = ref(false)
const editingOrder = ref<any>(null)
const customerOptions = ref<{ label: string; value: number }[]>([])
const productOptions = ref<{ label: string; value: number }[]>([])
const productPriceMap = ref<Record<number, number>>({})
const search = ref('')

const showProductForm = ref(false)
const editingProductId = ref<number | null>(null)
const productForm = ref({ name: '', price: 0, description: '', category: '', unit: 'un', is_active: true })

onMounted(async () => {
  try {
    await Promise.all([store.fetchOrders(), loadProducts(), loadCustomers()])
  } catch (e) {
    toastError(e)
  }
  on('stock_updated', () => {
    store.fetchOrders()
    toast('success.stock_updated_by_kitchen', 'success')
  })
})

onUnmounted(() => {
  off('stock_updated')
})

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
  if (!confirm(t('page.vendas.confirm_delete', { customer: order.customer_name }))) return
  try {
    await store.deleteOrder(order.id)
    toast('success.order_deleted', 'success')
  } catch (e) {
    toastError(e)
  }
}

async function confirmPayment(orderId: number) {
  try {
    await store.updatePayment(orderId, 'paid')
  } catch (e) {
    toastError(e)
  }
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
  }).catch((e) => {
    toastError(e)
    showProductForm.value = false
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
  } catch (e) {
    toastError(e)
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
      <h2 class="text-xl font-semibold">{{ $t('page.vendas.title') }}</h2>
      <div class="flex gap-2 items-center">
        <input v-model="search" :placeholder="$t('page.vendas.search_placeholder')" class="border rounded px-3 py-1.5 text-sm" />
        <button class="bg-green-600 hover:bg-green-700 text-white font-semibold py-2 px-4 rounded text-sm" @click="showForm = true">
          {{ $t('page.vendas.new_order') }}
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
    />

    <o-modal v-model:active="showProductForm" :width="450">
      <div class="rounded-lg overflow-hidden">
        <div class="bg-green-700 text-white px-6 py-4 flex items-center justify-between">
          <h3 class="text-lg font-bold">{{ editingProductId ? $t('page.vendas.edit_product') : $t('page.vendas.new_product') }}</h3>
          <button class="text-white/80 hover:text-white text-xl leading-none" @click="showProductForm = false">&times;</button>
        </div>
        <form @submit.prevent="saveProduct" class="p-6 space-y-4">
          <o-field :label="$t('page.vendas.name')">
            <o-input v-model="productForm.name" required />
          </o-field>
          <div class="flex gap-4">
            <o-field :label="$t('page.vendas.price')" class="flex-1">
              <o-input v-model="productForm.price" type="number" step="0.1" min="0" required />
            </o-field>
            <o-field :label="$t('page.vendas.unit')" class="w-28">
              <select v-model="productForm.unit" class="w-full border rounded px-3 py-2 text-sm bg-white">
                <option value="un">{{ $t('unit.un') }}</option>
                <option value="serving">{{ $t('unit.serving') }}</option>
                <option value="kg">{{ $t('unit.kg') }}</option>
                <option value="L">{{ $t('unit.L') }}</option>
              </select>
            </o-field>
          </div>
          <o-field :label="$t('page.vendas.category')">
            <select v-model="productForm.category" class="w-full border rounded px-3 py-2 text-sm bg-white">
              <option value="">{{ $t('page.vendas.no_category') }}</option>
              <option value="meal_box">{{ $t('page.vendas.meal_box') }}</option>
              <option value="side_dish">{{ $t('page.vendas.side_dish') }}</option>
              <option value="juice">{{ $t('page.vendas.juice') }}</option>
              <option value="brownie">{{ $t('page.vendas.brownie') }}</option>
              <option value="broth">{{ $t('page.vendas.broth') }}</option>
            </select>
          </o-field>
          <o-field :label="$t('page.vendas.description')">
            <o-input v-model="productForm.description" type="textarea" />
          </o-field>
          <label class="flex items-center gap-2 cursor-pointer select-none">
            <input type="checkbox" v-model="productForm.is_active" class="w-4 h-4 rounded border-gray-300 text-green-600 focus:ring-green-500" />
            <span class="text-sm font-medium text-gray-700">{{ $t('page.vendas.active') }}</span>
          </label>
          <div class="flex justify-end gap-3 pt-2 border-t">
            <button type="button" class="bg-gray-200 hover:bg-gray-300 text-gray-700 font-semibold py-2 px-6 rounded" @click="showProductForm = false">
              {{ $t('page.vendas.cancel') }}
            </button>
            <button type="submit" class="bg-green-600 hover:bg-green-700 text-white font-semibold py-2 px-6 rounded shadow-sm">
              {{ $t('page.vendas.save') }}
            </button>
          </div>
        </form>
      </div>
    </o-modal>

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
