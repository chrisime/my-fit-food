<script setup lang="ts">
import { ref, onMounted } from 'vue'

const API = '/api'
const token = () => localStorage.getItem('token') || ''

interface User {
  id: number
  username: string
  full_name: string
  role: string
  is_active: boolean
}

const users = ref<User[]>([])
const showModal = ref(false)
const isEditing = ref(false)
const editingUser = ref<User | null>(null)
const form = ref({ username: '', password: '', full_name: '', role: 'vendas' })

onMounted(loadUsers)

async function loadUsers() {
  const res = await fetch(`${API}/auth/users`, {
    method: 'GET',
    headers: { Authorization: `Bearer ${token()}` },
  })
  if (res.ok) users.value = await res.json()
}

function openNew() {
  isEditing.value = false
  editingUser.value = null
  form.value = { username: '', password: '', full_name: '', role: 'vendas' }
  showModal.value = true
}

function openEdit(u: User) {
  isEditing.value = true
  editingUser.value = u
  form.value = { username: u.username, password: '', full_name: u.full_name, role: u.role }
  showModal.value = true
}

async function deleteUser(u: User) {
  if (!confirm(`Excluir "${u.full_name}" (${u.username})?`)) return
  const res = await fetch(`${API}/auth/users/${u.id}`, {
    method: 'DELETE',
    headers: { Authorization: `Bearer ${token()}` },
  })
  if (!res.ok) {
    const msg = await res.json().then((d) => d.detail).catch(() => 'Erro ao excluir')
    alert(msg)
  }
  await loadUsers()
}

async function saveUser() {
  const url = isEditing.value ? `${API}/auth/users/${editingUser.value!.id}` : `${API}/auth/users`
  const method = isEditing.value ? 'PUT' : 'POST'
  const body = isEditing.value
    ? { username: form.value.username, full_name: form.value.full_name, role: form.value.role, password: form.value.password || undefined }
    : form.value
  const res = await fetch(url, {
    method,
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token()}` },
    body: JSON.stringify(body),
  })
  if (res.ok) {
    showModal.value = false
    form.value = { username: '', password: '', full_name: '', role: 'vendas' }
    await loadUsers()
  } else {
    const err = await res.json().then((d) => d.detail).catch(() => 'Erro')
    alert(err)
  }
}
</script>

<template>
  <div>
    <div class="flex justify-between items-center mb-4">
      <h2 class="text-xl font-semibold">Usuários</h2>
      <button class="bg-green-600 hover:bg-green-700 text-white font-semibold py-2 px-4 rounded text-sm" @click="openNew">
        Novo Usuário
      </button>
    </div>

    <div class="bg-white rounded shadow overflow-hidden">
      <table class="w-full text-sm">
        <thead class="bg-gray-100">
          <tr>
            <th class="text-left p-3">Nome</th>
            <th class="text-left p-3">Usuário</th>
            <th class="text-center p-3">Papel</th>
            <th class="text-center p-3">Ativo</th>
            <th class="text-center p-3"></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="u in users" :key="u.id" class="border-t">
            <td class="p-3 font-medium">{{ u.full_name }}</td>
            <td class="p-3 text-gray-500">{{ u.username }}</td>
            <td class="p-3 text-center">
              <span class="text-xs font-semibold px-2 py-0.5 rounded"
                :class="u.role === 'admin' ? 'bg-purple-100 text-purple-700' : u.role === 'cozinha' ? 'bg-blue-100 text-blue-700' : 'bg-green-100 text-green-700'"
              >
                {{ u.role }}
              </span>
            </td>
            <td class="p-3 text-center">
              <span class="text-xs" :class="u.is_active ? 'text-green-600' : 'text-red-600'">
                {{ u.is_active ? 'Sim' : 'Não' }}
              </span>
            </td>
            <td class="p-3 text-center flex gap-2 justify-center">
              <button class="text-blue-600 hover:text-blue-800" title="Editar" @click="openEdit(u)"><i class="mdi mdi-pencil"></i></button>
              <button class="text-red-600 hover:text-red-800" title="Excluir" @click="deleteUser(u)"><i class="mdi mdi-delete"></i></button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <o-modal v-model:active="showModal" :width="500">
      <div class="rounded-lg overflow-hidden">
        <div class="bg-green-700 text-white px-6 py-4 flex items-center justify-between">
          <h3 class="text-lg font-bold">{{ isEditing ? 'Editar Usuário' : 'Novo Usuário' }}</h3>
          <button class="text-white/80 hover:text-white text-xl leading-none" @click="showModal = false">&times;</button>
        </div>
        <form @submit.prevent="saveUser" class="p-6 space-y-4">
          <o-field label="Nome completo">
            <o-input v-model="form.full_name" required />
          </o-field>
          <o-field label="Usuário">
            <o-input v-model="form.username" required />
          </o-field>
          <o-field label="Senha">
            <o-input v-model="form.password" type="password" :required="!isEditing" password-reveal />
            <p v-if="isEditing" class="text-xs text-gray-400 mt-1">Deixe em branco para manter a senha atual</p>
          </o-field>
          <o-field label="Papel">
            <select v-model="form.role" class="w-full border rounded px-3 py-2 text-sm bg-white">
              <option value="vendas">Vendas</option>
              <option value="cozinha">Cozinha</option>
              <option value="admin">Admin</option>
            </select>
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
