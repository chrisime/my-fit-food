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
        <h3 class="text-lg font-bold">{{ $t('order_form.title') }}</h3>
        <o-button variant="ghost" class="text-white/80" @click="emit('close')">&times;</o-button>
      </div>
      <form @submit.prevent="submitOrder" class="p-6 space-y-4">
        <o-field :label="$t('order_form.existing_customer')">
          <div class="flex gap-1">
            <o-select v-model="selectedCustomerId" @change="selectCustomer">
              <option :value="0">{{ $t('order_form.select_customer') }}</option>
              <option v-for="c in customerOptions" :key="c.value" :value="c.value">{{ c.label }}</option>
            </o-select>
            <o-button variant="ghost" class="text-green-700" :title="$t('order_form.new_customer_title')" @click="$router.push('/customers')">+</o-button>
          </div>
        </o-field>
        <div class="grid grid-cols-2 gap-4">
          <o-field :label="$t('order_form.customer_name')">
            <o-input v-model="customerName" required />
          </o-field>
          <o-field :label="$t('order_form.whatsapp')">
            <o-input v-model="customerPhone" :placeholder="$t('order_form.phone_placeholder')" />
          </o-field>
        </div>
        <div class="border rounded-lg p-3 bg-gray-50 space-y-3">
          <p class="text-sm font-semibold text-gray-600">{{ $t('order_form.delivery_address') }}</p>
          <div v-if="customerData?.address2_street" class="flex gap-4 mb-3">
            <o-radio v-model="selectedAddress" :native-value="'1'" @change="applyAddress('1')">
              {{ $t('order_form.address_1') }}
            </o-radio>
            <o-radio v-model="selectedAddress" :native-value="'2'" @change="applyAddress('2')">
              {{ $t('order_form.address_2') }}
            </o-radio>
          </div>
          <o-field :label="$t('order_form.street')">
            <o-input v-model="addressStreet" :placeholder="$t('order_form.street_placeholder')" />
          </o-field>
          <div class="grid grid-cols-2 gap-4">
            <o-field :label="$t('order_form.neighborhood')">
              <o-input v-model="addressNeighborhood" :placeholder="$t('order_form.n_placeholder')" />
            </o-field>
            <o-field :label="$t('order_form.city')">
              <o-input v-model="addressCity" :placeholder="$t('order_form.city_placeholder')" />
            </o-field>
          </div>
        </div>
        <o-field :label="$t('order_form.notes')">
          <o-input v-model="notes" type="textarea" />
        </o-field>
        <div class="border rounded-lg p-4 bg-gray-50 space-y-3">
          <p class="text-sm font-semibold text-gray-600">{{ $t('order_form.items') }}</p>
          <div v-for="(item, i) in items" :key="i" class="flex gap-3 items-end">
            <o-field :label="$t('order_form.product')" class="flex-1">
              <div class="flex gap-1">
                <o-select v-model="item.product_id">
                  <option :value="0" disabled>{{ $t('order_form.select') }}</option>
                  <option v-for="p in productOptions" :key="p.value" :value="p.value">
                    {{ p.label }}
                  </option>
                </o-select>
                <o-button variant="ghost" class="text-green-700" :title="$t('order_form.new_product_title')" @click="emit('new-product')">+</o-button>
              </div>
            </o-field>
            <o-field :label="$t('order_form.qty')" class="w-24">
              <o-input v-model="item.quantity" type="number" min="1" />
            </o-field>
            <div class="flex items-center gap-1 text-xs whitespace-nowrap mb-1" style="padding-bottom:2px">
              <o-checkbox v-model="item.is_free" />
              {{ $t('order_form.free') }}
            </div>
          </div>
          <o-button variant="ghost" class="text-green-700 font-semibold" @click="addItem">{{ $t('order_form.add_item') }}</o-button>
        </div>
        <div class="text-right text-lg font-bold text-green-700">
          {{ $t('order_form.total') }} R$ {{ totalAmount.toFixed(2) }}
        </div>
        <div class="flex justify-end gap-3 pt-2 border-t">
          <o-button @click="emit('close')">
            {{ $t('order_form.cancel') }}
          </o-button>
          <o-button variant="primary" type="submit">
            {{ $t('order_form.save') }}
          </o-button>
        </div>
      </form>
    </div>
  </o-modal>
</template>
