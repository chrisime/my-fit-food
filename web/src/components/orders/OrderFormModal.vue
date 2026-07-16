<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { get, post } from '@/composables/api'
import { useOrderStore } from '@/stores/orders'

const store = useOrderStore()

const props = defineProps<{
  active: boolean
  productOptions: { label: string; value: number }[]
  customerOptions: { label: string; value: number }[]
  productPriceMap: Record<number, number>
}>()

const emit = defineEmits<{
  close: []
  saved: []
  'new-product': []
}>()

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

const totalAmount = computed(() =>
  items.value.reduce((sum, item) => {
    if (item.is_free) return sum
    const price = props.productPriceMap[item.product_id] || 0
    return sum + price * item.quantity
  }, 0)
)

watch(() => props.active, (val) => {
  if (!val) return
  selectedCustomerId.value = 0
  customerData.value = null
  selectedAddress.value = '1'
  customerName.value = ''
  customerPhone.value = ''
  addressStreet.value = ''
  addressNeighborhood.value = ''
  addressCity.value = ''
  notes.value = ''
  items.value = [{ product_id: 0, quantity: 1, is_free: false }]
})

async function selectCustomer() {
  const id = selectedCustomerId.value
  if (!id) return
  const c = await get(`/customers/${id}`)
  customerData.value = c
  customerName.value = c.name
  customerPhone.value = c.phone || ''
  selectedAddress.value = '1'
  applyAddress('1')
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
    emit('saved')
    emit('close')
  } catch {
    // toast handled by parent
  }
}
</script>

<template>
  <o-modal :active="active" :width="700" :content-class="'w-full'" @update:active="(v: boolean) => !v && emit('close')">
    <div class="rounded-lg overflow-hidden">
      <div class="bg-green-700 text-white px-6 py-4 flex items-center justify-between">
        <h3 class="text-lg font-bold">Novo Pedido</h3>
        <button class="text-white/80 hover:text-white text-xl leading-none" @click="emit('close')">&times;</button>
      </div>
      <form @submit.prevent="submitOrder" class="p-6 space-y-4">
        <o-field label="Cliente existente">
          <div class="flex gap-1">
            <select v-model="selectedCustomerId" class="flex-1 border rounded px-3 py-2 text-sm bg-white" @change="selectCustomer">
              <option :value="0">Selecione um cliente...</option>
              <option v-for="c in customerOptions" :key="c.value" :value="c.value">{{ c.label }}</option>
            </select>
            <button type="button" title="Cadastrar novo cliente" class="text-green-700 hover:text-green-800 text-lg leading-none px-1" @click="$router.push('/customers')">+</button>
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
                <button type="button" title="Novo produto" class="text-green-700 hover:text-green-800 text-lg leading-none px-1" @click="emit('new-product')">+</button>
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
          <button type="button" class="bg-gray-200 hover:bg-gray-300 text-gray-700 font-semibold py-2 px-6 rounded" @click="emit('close')">
            Cancelar
          </button>
          <button type="submit" class="bg-green-600 hover:bg-green-700 text-white font-semibold py-2 px-6 rounded shadow-sm">
            Salvar Pedido
          </button>
        </div>
      </form>
    </div>
  </o-modal>
</template>
