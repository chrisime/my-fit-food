<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useWebSocket } from '@/composables/useWebSocket'
import { get, post } from '@/composables/api'

const role = ref(localStorage.getItem('role') || '')
const isAdmin = computed(() => role.value === 'admin')
const isCozinha = computed(() => role.value === 'cozinha')
const canWrite = computed(() => isAdmin.value || isCozinha.value)

const stockBalance = ref<{ product_id: number; product_name: string; balance: number; unit: string }[]>([])
const productOptions = ref<{ label: string; value: number }[]>([])

const showProdForm = ref(false)
const showAdjustForm = ref(false)

const prodProductId = ref(0)
const prodQuantity = ref(1)
const prodNotes = ref('')

const adjustProductId = ref(0)
const adjustType = ref<'in' | 'out'>('in')
const adjustQuantity = ref(1)
const adjustNotes = ref('')

const toast = ref<{ show: boolean; message: string; type: 'success' | 'error' }>({ show: false, message: '', type: 'success' })
let toastTimer: ReturnType<typeof setTimeout> | null = null

const { on, off } = useWebSocket()

function showToast(message: string, type: 'success' | 'error' = 'success') {
  toast.value = { show: true, message, type }
  if (toastTimer) clearTimeout(toastTimer)
  toastTimer = setTimeout(() => { toast.value.show = false }, 4000)
}

onMounted(async () => {
  await Promise.all([fetchBalance(), loadProducts()])
  on('stock_updated', fetchBalance)
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
</script>

<template>
  <div>
    <div class="flex justify-between items-center mb-4">
      <h2 class="text-xl font-semibold">Estoque</h2>
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

    <div class="space-y-6">
      <form v-if="showProdForm && canWrite" @submit.prevent="submitProduction" class="border rounded-lg p-4 space-y-3 bg-gray-50">
        <p class="text-sm font-semibold text-gray-600">Registrar Produção</p>
        <div class="flex gap-4">
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

      <form v-if="showAdjustForm && canWrite" @submit.prevent="submitAdjust" class="border rounded-lg p-4 space-y-3 bg-gray-50">
        <p class="text-sm font-semibold text-gray-600">Ajuste de Estoque</p>
        <div class="flex gap-4">
          <o-field label="Produto" class="flex-1">
            <select v-model="adjustProductId" class="w-full border rounded px-3 py-2 text-sm bg-white" required>
              <option :value="0" disabled>Selecione</option>
              <option v-for="p in productOptions" :key="p.value" :value="p.value">{{ p.label }}</option>
            </select>
          </o-field>
          <o-field v-if="isAdmin" label="Tipo" class="w-32">
            <select v-model="adjustType" class="w-full border rounded px-3 py-2 text-sm bg-white">
              <option value="in">Entrada</option>
              <option value="out">Saída</option>
            </select>
          </o-field>
          <o-field v-else label="Tipo" class="w-32">
            <div class="w-full border rounded px-3 py-2 text-sm bg-gray-100 text-gray-500">Entrada</div>
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

      <div>
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
              <td class="py-2 text-right font-mono">—</td>
              <td class="py-2 text-right font-mono">—</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-if="canWrite" class="flex justify-center gap-4 pt-2 border-t">
        <button
          type="button"
          :title="showProdForm ? 'Fechar produção' : 'Produzir'"
          class="p-2 rounded-full hover:bg-gray-200"
          :class="showProdForm ? 'text-green-600 bg-green-100' : 'text-gray-600'"
          @click="showProdForm = !showProdForm"
        ><i class="mdi mdi-plus-circle text-2xl"></i></button>
        <button
          type="button"
          :title="showAdjustForm ? 'Fechar ajuste' : 'Ajustar'"
          class="p-2 rounded-full hover:bg-gray-200"
          :class="showAdjustForm ? 'text-green-600 bg-green-100' : 'text-gray-600'"
          @click="showAdjustForm = !showAdjustForm"
        ><i class="mdi mdi-tune text-2xl"></i></button>
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
