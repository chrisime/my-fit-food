<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useToast } from '@/composables/useToast'
import { get, post, put, del } from '@/composables/api'
import { useI18n } from 'vue-i18n'

const { toast, toastError } = useToast()
const { t } = useI18n()

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
const form = ref({ username: '', password: '', full_name: '', role: 'sales' })

onMounted(async () => {
  try {
    await loadUsers()
  } catch (e) {
    toastError(e)
  }
})

async function loadUsers() {
  users.value = await get<User[]>('/auth/users')
}

function openNew() {
  isEditing.value = false
  editingUser.value = null
  form.value = { username: '', password: '', full_name: '', role: 'sales' }
  showModal.value = true
}

function openEdit(u: User) {
  isEditing.value = true
  editingUser.value = u
  form.value = { username: u.username, password: '', full_name: u.full_name, role: u.role }
  showModal.value = true
}

async function deleteUser(u: User) {
  if (!confirm(t('page.users.confirm_delete', { name: u.full_name, username: u.username }))) return
  try {
    await del(`/auth/users/${u.id}`)
    await loadUsers()
  } catch (e) {
    toastError(e)
  }
}

async function saveUser() {
  const body = isEditing.value
    ? { username: form.value.username, full_name: form.value.full_name, role: form.value.role, password: form.value.password || undefined }
    : form.value
  try {
    if (isEditing.value) {
      await put(`/auth/users/${editingUser.value!.id}`, body)
    } else {
      await post('/auth/users', body)
    }
    showModal.value = false
    form.value = { username: '', password: '', full_name: '', role: 'sales' }
    await loadUsers()
  } catch (e) {
    toastError(e)
  }
}
</script>

<template>
  <div>
    <div class="flex justify-between items-center mb-4">
      <h2 class="text-xl font-semibold">{{ $t('page.users.title') }}</h2>
      <button class="bg-green-600 hover:bg-green-700 text-white font-semibold py-2 px-4 rounded text-sm" @click="openNew">
        {{ $t('page.users.new') }}
      </button>
    </div>

    <div class="bg-white rounded shadow overflow-hidden">
      <table class="w-full text-sm">
        <thead class="bg-gray-100">
          <tr>
            <th class="text-left p-3">{{ $t('page.users.full_name') }}</th>
            <th class="text-left p-3">{{ $t('page.users.username') }}</th>
            <th class="text-center p-3">{{ $t('page.users.role') }}</th>
            <th class="text-center p-3">{{ $t('page.users.active') }}</th>
            <th class="text-center p-3"></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="u in users" :key="u.id" class="border-t">
            <td class="p-3 font-medium">{{ u.full_name }}</td>
            <td class="p-3 text-gray-500">{{ u.username }}</td>
            <td class="p-3 text-center">
              <span class="text-xs font-semibold px-2 py-0.5 rounded"
                :class="u.role === 'admin' ? 'bg-purple-100 text-purple-700' : u.role === 'kitchen' ? 'bg-blue-100 text-blue-700' : 'bg-green-100 text-green-700'"
              >
                {{ $t('role.' + u.role) }}
              </span>
            </td>
            <td class="p-3 text-center">
              <span class="text-xs" :class="u.is_active ? 'text-green-600' : 'text-red-600'">
                {{ u.is_active ? $t('page.users.active_yes') : $t('page.users.active_no') }}
              </span>
            </td>
            <td class="p-3 text-center flex gap-2 justify-center">
              <button class="text-blue-600 hover:text-blue-800" :title="$t('page.users.edit_title')" @click="openEdit(u)"><i class="mdi mdi-pencil"></i></button>
              <button class="text-red-600 hover:text-red-800" :title="$t('page.users.delete_title')" @click="deleteUser(u)"><i class="mdi mdi-delete"></i></button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <o-modal v-model:active="showModal" :width="500">
      <div class="rounded-lg overflow-hidden">
        <div class="bg-green-700 text-white px-6 py-4 flex items-center justify-between">
          <h3 class="text-lg font-bold">{{ isEditing ? $t('page.users.edit') : $t('page.users.new') }}</h3>
          <button class="text-white/80 hover:text-white text-xl leading-none" @click="showModal = false">&times;</button>
        </div>
        <form @submit.prevent="saveUser" class="p-6 space-y-4">
          <o-field :label="$t('page.users.full_name')">
            <o-input v-model="form.full_name" required />
          </o-field>
          <o-field :label="$t('page.users.username')">
            <o-input v-model="form.username" required />
          </o-field>
          <o-field :label="$t('page.users.password')">
            <o-input v-model="form.password" type="password" :required="!isEditing" password-reveal />
            <p v-if="isEditing" class="text-xs text-gray-400 mt-1">{{ $t('page.users.password_keep') }}</p>
          </o-field>
          <o-field :label="$t('page.users.role')">
            <select v-model="form.role" class="w-full border rounded px-3 py-2 text-sm bg-white">
              <option value="sales">{{ $t('role.sales') }}</option>
              <option value="kitchen">{{ $t('role.kitchen') }}</option>
              <option value="admin">{{ $t('role.admin') }}</option>
            </select>
          </o-field>
          <div class="flex justify-end gap-3 pt-2 border-t">
            <button type="button" class="bg-gray-200 hover:bg-gray-300 text-gray-700 font-semibold py-2 px-6 rounded" @click="showModal = false">
              {{ $t('page.users.cancel') }}
            </button>
            <button type="submit" class="bg-green-600 hover:bg-green-700 text-white font-semibold py-2 px-6 rounded shadow-sm">
              {{ $t('page.users.save') }}
            </button>
          </div>
        </form>
      </div>
    </o-modal>
  </div>
</template>
