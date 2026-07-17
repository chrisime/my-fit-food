<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useOrderStore, type Order } from '@/stores/orders'
import { useI18n } from 'vue-i18n'

const store = useOrderStore()
const { t } = useI18n()

const props = defineProps<{
  active: boolean
  order: Order | null
  productOptions: { label: string; value: number }[]
  productPriceMap: Record<number, number>
}>()

const emit = defineEmits<{
  close: []
  saved: []
  error: [message: string]
}>()

const editItems = ref<{ product_id: number; quantity: number; is_free: boolean }[]>([])
const editNotes = ref('')

watch(() => props.active, (val) => {
  if (val && props.order) {
    editNotes.value = props.order.notes || ''
    editItems.value = props.order.items.map((i) => ({
      product_id: i.product_id,
      quantity: i.quantity,
      is_free: i.is_free,
    }))
  }
})

const editTotalAmount = computed(() =>
  editItems.value.reduce((sum, item) => {
    if (item.is_free) return sum
    const price = props.productPriceMap[item.product_id] || 0
    return sum + price * item.quantity
  }, 0)
)

async function submitEditOrder() {
  if (!props.order) return
  try {
    await store.updateOrder(props.order.id, {
      notes: editNotes.value,
      items: editItems.value.filter((i) => i.product_id > 0),
    })
    emit('saved')
    emit('close')
  } catch {
    emit('error', t('error.unknown'))
  }
}
</script>

<template>
  <o-modal :active="active" :width="600" @update:active="(v: boolean) => !v && emit('close')">
    <div class="rounded-lg overflow-hidden">
      <div class="bg-green-700 text-white px-6 py-4 flex items-center justify-between">
        <h3 class="text-lg font-bold">{{ $t('edit_order.title', { customer: order?.customer_name }) }}</h3>
        <o-button variant="ghost" class="text-white/80" @click="emit('close')">&times;</o-button>
      </div>
      <form @submit.prevent="submitEditOrder" class="p-6 space-y-4">
        <o-field :label="$t('edit_order.notes')">
          <o-input v-model="editNotes" type="textarea" />
        </o-field>
        <div class="border rounded-lg p-4 bg-gray-50 space-y-3">
          <p class="text-sm font-semibold text-gray-600">{{ $t('edit_order.items') }}</p>
          <div v-for="(item, i) in editItems" :key="i" class="flex gap-3 items-end">
            <o-field :label="$t('edit_order.product')" class="flex-1">
              <o-select v-model="item.product_id" expanded>
                <option :value="0" disabled>{{ $t('edit_order.select') }}</option>
                <option v-for="p in productOptions" :key="p.value" :value="p.value">{{ p.label }}</option>
              </o-select>
            </o-field>
            <o-field :label="$t('edit_order.qty')" class="w-24">
              <o-input v-model="item.quantity" type="number" min="1" />
            </o-field>
            <o-checkbox v-model="item.is_free" class="mb-1">{{ $t('edit_order.free') }}</o-checkbox>
          </div>
          <o-button variant="ghost" class="text-green-700 font-semibold" @click="editItems.push({ product_id: 0, quantity: 1, is_free: false })">{{ $t('edit_order.add_item') }}</o-button>
        </div>
        <div class="text-right text-lg font-bold text-green-700">
          {{ $t('edit_order.total') }} R$ {{ editTotalAmount.toFixed(2) }}
        </div>
        <div class="flex justify-end gap-3 pt-2 border-t">
          <o-button @click="emit('close')">{{ $t('edit_order.cancel') }}</o-button>
          <o-button variant="primary" type="submit">{{ $t('edit_order.save') }}</o-button>
        </div>
      </form>
    </div>
  </o-modal>
</template>
