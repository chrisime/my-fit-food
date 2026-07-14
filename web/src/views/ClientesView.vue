<script setup lang="ts">
import { ref, onMounted } from 'vue'

const API = '/api'
const token = () => localStorage.getItem('token') || ''

interface Customer {
  id: number
  name: string
  phone: string | null
  address_street: string | null
  address_neighborhood: string | null
  address_city: string | null
  address2_street: string | null
  address2_neighborhood: string | null
  address2_city: string | null
  notes: string | null
  created_at: string
}

const customers = ref<Customer[]>([])
const showModal = ref(false)
const editingId = ref<number | null>(null)
const form = ref({ name: '', phone: '', address_street: '', address_neighborhood: '', address_city: '', address2_street: '', address2_neighborhood: '', address2_city: '', notes: '' })

onMounted(loadCustomers)

async function loadCustomers() {
  const res = await fetch(`${API}/customers/`, {
    headers: { Authorization: `Bearer ${token()}` },
  })
  if (res.ok) customers.value = await res.json()
}

function openNew() {
  editingId.value = null
  form.value = { name: '', phone: '', address_street: '', address_neighborhood: '', address_city: '', address2_street: '', address2_neighborhood: '', address2_city: '', notes: '' }
  showModal.value = true
}

function openEdit(c: Customer) {
  editingId.value = c.id
  form.value = {
    name: c.name,
    phone: c.phone || '',
    address_street: c.address_street || '',
    address_neighborhood: c.address_neighborhood || '',
    address_city: c.address_city || '',
    address2_street: c.address2_street || '',
    address2_neighborhood: c.address2_neighborhood || '',
    address2_city: c.address2_city || '',
    notes: c.notes || '',
  }
  showModal.value = true
}

async function save() {
  const body = {
    ...form.value,
    phone: form.value.phone || null,
    address_street: form.value.address_street || null,
    address_neighborhood: form.value.address_neighborhood || null,
    address_city: form.value.address_city || null,
    address2_street: form.value.address2_street || null,
    address2_neighborhood: form.value.address2_neighborhood || null,
    address2_city: form.value.address2_city || null,
    notes: form.value.notes || null,
  }
  const url = editingId.value ? `${API}/customers/${editingId.value}` : `${API}/customers/`
  const method = editingId.value ? 'PUT' : 'POST'
  const res = await fetch(url, {
    method,
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token()}` },
    body: JSON.stringify(body),
  })
  if (res.ok) {
    showModal.value = false
    await loadCustomers()
  }
}

async function deleteCustomer(c: Customer) {
  if (!confirm(`Excluir "${c.name}"?`)) return
  const res = await fetch(`${API}/customers/${c.id}`, {
    method: 'DELETE',
    headers: { Authorization: `Bearer ${token()}` },
  })
  if (!res.ok) alert('Erro ao excluir cliente')
  await loadCustomers()
}
</script>

<template>
  <div>
    <div class="flex justify-between items-center mb-4">
      <h2 class="text-xl font-semibold">Clientes</h2>
      <button class="bg-green-600 hover:bg-green-700 text-white font-semibold py-2 px-4 rounded text-sm" @click="openNew">
        Novo Cliente
      </button>
    </div>

    <div class="bg-white rounded-lg shadow-sm border overflow-hidden">
      <table class="w-full text-sm">
        <thead>
          <tr class="border-b bg-gray-50 text-left">
            <th class="py-3 px-4">Nome</th>
            <th class="py-3 px-4">Telefone</th>
            <th class="py-3 px-4">Endereço</th>
            <th class="py-3 px-4">Observações</th>
            <th class="py-3 px-4 w-24"></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="c in customers" :key="c.id" class="border-b hover:bg-gray-50">
            <td class="py-3 px-4 font-medium">{{ c.name }}</td>
            <td class="py-3 px-4 text-gray-600">{{ c.phone || '—' }}</td>
            <td class="py-3 px-4 text-gray-600 text-xs">
              <div>{{ [c.address_street, c.address_neighborhood, c.address_city].filter(Boolean).join(', ') || '—' }}</div>
              <div v-if="c.address2_street" class="mt-1 text-gray-400">{{ [c.address2_street, c.address2_neighborhood, c.address2_city].filter(Boolean).join(', ') }}</div>
            </td>
            <td class="py-3 px-4 text-gray-500 text-xs max-w-[200px] truncate">{{ c.notes || '—' }}</td>
            <td class="py-3 px-4">
              <button class="text-blue-600 hover:text-blue-800 mr-2" title="Editar" @click="openEdit(c)"><i class="mdi mdi-pencil"></i></button>
              <button class="text-red-600 hover:text-red-800" title="Excluir" @click="deleteCustomer(c)"><i class="mdi mdi-delete"></i></button>
            </td>
          </tr>
          <tr v-if="!customers.length">
            <td colspan="5" class="py-8 text-center text-gray-400">Nenhum cliente cadastrado</td>
          </tr>
        </tbody>
      </table>
    </div>

    <o-modal v-model:active="showModal" :width="500">
      <div class="rounded-lg overflow-hidden">
        <div class="bg-green-700 text-white px-6 py-4 flex items-center justify-between">
          <h3 class="text-lg font-bold">{{ editingId ? 'Editar' : 'Novo' }} Cliente</h3>
          <button class="text-white/80 hover:text-white text-xl leading-none" @click="showModal = false">&times;</button>
        </div>
        <form @submit.prevent="save" class="p-6 space-y-4">
          <o-field label="Nome">
            <o-input v-model="form.name" required />
          </o-field>
          <o-field label="Telefone">
            <o-input v-model="form.phone" placeholder="(11) 99999-9999" />
          </o-field>
          <div class="border rounded-lg p-3 bg-gray-50 space-y-3">
            <p class="text-sm font-semibold text-gray-600">Endereço 1</p>
            <o-field label="Rua, Número">
              <o-input v-model="form.address_street" />
            </o-field>
            <div class="grid grid-cols-2 gap-4">
              <o-field label="Bairro">
                <o-input v-model="form.address_neighborhood" />
              </o-field>
              <o-field label="Cidade">
                <o-input v-model="form.address_city" />
              </o-field>
            </div>
          </div>
          <div class="border rounded-lg p-3 bg-gray-50 space-y-3">
            <p class="text-sm font-semibold text-gray-600">Endereço 2 <span class="text-xs font-normal text-gray-400">(opcional)</span></p>
            <o-field label="Rua, Número">
              <o-input v-model="form.address2_street" />
            </o-field>
            <div class="grid grid-cols-2 gap-4">
              <o-field label="Bairro">
                <o-input v-model="form.address2_neighborhood" />
              </o-field>
              <o-field label="Cidade">
                <o-input v-model="form.address2_city" />
              </o-field>
            </div>
          </div>
          <o-field label="Observações">
            <o-input v-model="form.notes" type="textarea" />
          </o-field>
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
