<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useToast } from '@/composables/useToast'
import { get, post, put, del } from '@/composables/api'
import { useI18n } from 'vue-i18n'

const { toast, toastError } = useToast()
const { t } = useI18n()

interface Product {
  id: number
  name: string
  description: string | null
  price: number
  category: string | null
  unit: string
  is_active: boolean
}

const products = ref<Product[]>([])
const showModal = ref(false)
const editing = ref<Partial<Product> | null>(null)
const isNew = ref(true)

const form = ref({
  name: '',
  description: '',
  price: 0,
  category: '',
  unit: 'un' as string,
  is_active: true,
})

onMounted(async () => {
  try {
    await loadProducts()
  } catch (e) {
    toastError(e)
  }
})

async function loadProducts() {
  products.value = await get<Product[]>('/products/?active_only=false')
}

function openNew() {
  isNew.value = true
  editing.value = null
  form.value = { name: '', description: '', price: 0, category: '', unit: 'un', is_active: true }
  showModal.value = true
}

function openEdit(p: Product) {
  isNew.value = false
  editing.value = p
  form.value = {
    name: p.name,
    description: p.description || '',
    price: p.price,
    category: p.category || '',
    unit: p.unit,
    is_active: p.is_active,
  }
  showModal.value = true
}

async function save() {
  const body = { ...form.value, description: form.value.description || null, category: form.value.category || null }
  try {
    if (isNew.value) {
      await post('/products/', body)
    } else {
      await put(`/products/${editing.value!.id}`, body)
    }
    showModal.value = false
    await loadProducts()
  } catch (e) {
    toastError(e)
  }
}

async function deleteProduct(p: Product) {
  if (!confirm(t('page.products.confirm_delete', { name: p.name }))) return
  try {
    await del(`/products/${p.id}`)
    await loadProducts()
  } catch (e) {
    toastError(e)
  }
}

async function toggleActive(p: Product) {
  try {
    await put(`/products/${p.id}`, { is_active: !p.is_active })
    await loadProducts()
  } catch (e) {
    toastError(e)
  }
}
</script>

<template>
  <div>
    <div class="flex justify-between items-center mb-4">
      <h2 class="text-xl font-semibold">{{ $t('page.products.title') }}</h2>
      <o-button variant="primary" icon-left="plus" class="font-semibold" @click="openNew">
        {{ $t('page.products.new') }}
      </o-button>
    </div>

    <div class="bg-white rounded shadow overflow-hidden">
      <table class="w-full text-sm">
        <thead class="bg-gray-100">
          <tr>
            <th class="text-left p-3">{{ $t('page.products.name') }}</th>
            <th class="text-left p-3">{{ $t('page.products.category') }}</th>
            <th class="text-right p-3">{{ $t('page.products.price') }}</th>
            <th class="text-center p-3">{{ $t('page.products.unit') }}</th>
            <th class="text-center p-3">{{ $t('page.products.active') }}</th>
            <th class="text-center p-3"></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="p in products" :key="p.id" class="border-t" :class="{ 'opacity-50': !p.is_active }">
            <td class="p-3 font-medium">{{ p.name }}</td>
            <td class="p-3 text-gray-500">{{ p.category ? $t('page.vendas.' + p.category) : $t('page.products.no_category') }}</td>
            <td class="p-3 text-right font-mono">R$ {{ p.price.toFixed(2) }}</td>
            <td class="p-3 text-center">{{ $t('unit.' + p.unit) }}</td>
            <td class="p-3 text-center">
              <o-button
                size="small"
                :variant="p.is_active ? 'primary' : 'danger'"
                @click="toggleActive(p)"
              >
                {{ p.is_active ? $t('page.products.active_yes') : $t('page.products.active_no') }}
              </o-button>
            </td>
            <td class="p-3 text-center flex gap-2 justify-center">
              <o-button variant="info" size="small" :title="$t('page.products.edit_title')" @click="openEdit(p)"><i class="mdi mdi-pencil"></i></o-button>
              <o-button variant="danger" size="small" :title="$t('page.products.delete_title')" @click="deleteProduct(p)"><i class="mdi mdi-delete"></i></o-button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <o-modal v-model:active="showModal" :width="550">
      <div class="rounded-lg overflow-hidden">
        <div class="bg-green-700 text-white px-6 py-4 flex items-center justify-between">
          <h3 class="text-lg font-bold">{{ isNew ? $t('page.products.new') : $t('page.products.edit') }}</h3>
          <o-button variant="ghost" class="text-white/80" @click="showModal = false">&times;</o-button>
        </div>
        <form @submit.prevent="save" class="p-6 space-y-4">
          <o-field :label="$t('page.products.name')">
            <o-input v-model="form.name" required />
          </o-field>
          <div class="flex gap-4 items-start">
            <o-field :label="$t('page.products.category')" class="flex-1">
              <o-select v-model="form.category">
                <option value="">{{ $t('page.products.no_category') }}</option>
                <option value="meal_box">{{ $t('page.vendas.meal_box') }}</option>
                <option value="side_dish">{{ $t('page.vendas.side_dish') }}</option>
                <option value="juice">{{ $t('page.vendas.juice') }}</option>
                <option value="brownie">{{ $t('page.vendas.brownie') }}</option>
                <option value="broth">{{ $t('page.vendas.broth') }}</option>
              </o-select>
            </o-field>
            <o-field :label="$t('page.products.price')" class="w-32">
              <o-input v-model="form.price" type="number" step="0.1" min="0" required />
            </o-field>
            <o-field :label="$t('page.products.unit')" class="w-28">
              <o-select v-model="form.unit">
                <option value="un">{{ $t('unit.un') }}</option>
                <option value="serving">{{ $t('unit.serving') }}</option>
                <option value="kg">{{ $t('unit.kg') }}</option>
                <option value="L">{{ $t('unit.L') }}</option>
              </o-select>
            </o-field>
          </div>
          <o-field :label="$t('page.products.description')">
            <o-input v-model="form.description" type="textarea" />
          </o-field>
          <label class="flex items-center gap-2 cursor-pointer select-none">
            <o-checkbox v-model="form.is_active" />
            <span class="text-sm font-medium text-gray-700">{{ $t('page.products.active') }}</span>
          </label>
          <div class="flex justify-end gap-3 pt-2 border-t">
            <o-button type="button" @click="showModal = false">
              {{ $t('page.products.cancel') }}
            </o-button>
            <o-button variant="primary" type="submit">
              {{ $t('page.products.save') }}
            </o-button>
          </div>
        </form>
      </div>
    </o-modal>
  </div>
</template>
