<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { get, post, put, del } from '@/composables/api'
import { unitLabel } from '@/composables/labels'

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

onMounted(loadProducts)

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
  if (isNew.value) {
    await post('/products/', body)
  } else {
    await put(`/products/${editing.value!.id}`, body)
  }
  showModal.value = false
  await loadProducts()
}

async function deleteProduct(p: Product) {
  if (!confirm(`Excluir "${p.name}"?`)) return
  try {
    await del(`/products/${p.id}`)
  } catch {
    alert('Erro ao excluir')
  }
  await loadProducts()
}

async function toggleActive(p: Product) {
  await put(`/products/${p.id}`, { is_active: !p.is_active })
  await loadProducts()
}
</script>

<template>
  <div>
    <div class="flex justify-between items-center mb-4">
      <h2 class="text-xl font-semibold">Produtos</h2>
      <button class="bg-green-600 hover:bg-green-700 text-white font-semibold py-2 px-4 rounded" @click="openNew">
        Novo Produto
      </button>
    </div>

    <div class="bg-white rounded shadow overflow-hidden">
      <table class="w-full text-sm">
        <thead class="bg-gray-100">
          <tr>
            <th class="text-left p-3">Nome</th>
            <th class="text-left p-3">Categoria</th>
            <th class="text-right p-3">Preço</th>
            <th class="text-center p-3">Unidade</th>
            <th class="text-center p-3">Ativo</th>
            <th class="text-center p-3"></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="p in products" :key="p.id" class="border-t" :class="{ 'opacity-50': !p.is_active }">
            <td class="p-3 font-medium">{{ p.name }}</td>
            <td class="p-3 text-gray-500">{{ p.category || '-' }}</td>
            <td class="p-3 text-right font-mono">R$ {{ p.price.toFixed(2) }}</td>
            <td class="p-3 text-center">{{ unitLabel(p.unit) }}</td>
            <td class="p-3 text-center">
              <button
                class="text-xs font-semibold px-2 py-1 rounded"
                :class="p.is_active ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'"
                @click="toggleActive(p)"
              >
                {{ p.is_active ? 'Sim' : 'Não' }}
              </button>
            </td>
            <td class="p-3 text-center flex gap-2 justify-center">
              <button class="text-blue-600 hover:text-blue-800" title="Editar" @click="openEdit(p)"><i class="mdi mdi-pencil"></i></button>
              <button class="text-red-600 hover:text-red-800" title="Excluir" @click="deleteProduct(p)"><i class="mdi mdi-delete"></i></button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <o-modal v-model:active="showModal" :width="550">
      <div class="rounded-lg overflow-hidden">
        <div class="bg-green-700 text-white px-6 py-4 flex items-center justify-between">
          <h3 class="text-lg font-bold">{{ isNew ? 'Novo Produto' : 'Editar Produto' }}</h3>
          <button class="text-white/80 hover:text-white text-xl leading-none" @click="showModal = false">&times;</button>
        </div>
        <form @submit.prevent="save" class="p-6 space-y-4">
          <o-field label="Nome">
            <o-input v-model="form.name" required />
          </o-field>
          <o-field label="Categoria">
            <select v-model="form.category" class="w-full border rounded px-3 py-2 text-sm bg-white">
              <option value="">Sem categoria</option>
              <option value="marmita">Marmita</option>
              <option value="acompanhamento">Acompanhamento</option>
              <option value="suco">Suco</option>
              <option value="brownie">Brownie</option>
              <option value="caldo">Caldo</option>
            </select>
          </o-field>
          <div class="flex gap-4">
            <o-field label="Preço (R$)" class="flex-1">
              <o-input v-model="form.price" type="number" step="0.1" min="0" required />
            </o-field>
            <o-field label="Unidade" class="w-28">
              <select v-model="form.unit" class="w-full border rounded px-3 py-2 text-sm bg-white">
                <option value="un">un</option>
                <option value="serving">porção</option>
                <option value="kg">kg</option>
                <option value="L">L</option>
              </select>
            </o-field>
          </div>
          <o-field label="Descrição">
            <o-input v-model="form.description" type="textarea" />
          </o-field>
          <label class="flex items-center gap-2 cursor-pointer select-none">
            <input type="checkbox" v-model="form.is_active" class="w-4 h-4 rounded border-gray-300 text-green-600 focus:ring-green-500" />
            <span class="text-sm font-medium text-gray-700">Ativo</span>
          </label>
          <div class="flex justify-end gap-3 pt-2 border-t">
            <button type="button" class="bg-gray-200 hover:bg-gray-300 text-gray-700 font-semibold py-2 px-6 rounded" @click="showModal = false">
              Cancelar
            </button>
            <button type="submit" class="bg-green-600 hover:bg-green-700 text-white font-semibold py-2 px-6 rounded shadow-sm">
              Salvar
            </button>
          </div>
        </form>
      </div>
    </o-modal>
  </div>
</template>
