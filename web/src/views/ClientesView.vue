<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useToast } from '@/composables/useToast'
import { get, post, put, del } from '@/composables/api'
import { useI18n } from 'vue-i18n'

const { toast, toastError } = useToast()
const { t } = useI18n()

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

onMounted(async () => {
  try {
    await loadCustomers()
  } catch (e) {
    toastError(e)
  }
})

async function loadCustomers() {
  customers.value = await get<Customer[]>('/customers/')
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
  try {
    if (editingId.value) {
      await put(`/customers/${editingId.value}`, body)
    } else {
      await post('/customers/', body)
    }
    showModal.value = false
    await loadCustomers()
  } catch (e) {
    toastError(e)
  }
}

async function deleteCustomer(c: Customer) {
  if (!confirm(t('page.customers.confirm_delete', { name: c.name }))) return
  try {
    await del(`/customers/${c.id}`)
    await loadCustomers()
  } catch (e) {
    toastError(e)
  }
}
</script>

<template>
  <div>
    <div class="flex justify-between items-center mb-4">
      <h2 class="text-xl font-semibold">{{ $t('page.customers.title') }}</h2>
      <o-button variant="primary" icon-left="plus" class="font-semibold" @click="openNew">
        {{ $t('page.customers.new') }}
      </o-button>
    </div>

    <div class="bg-white rounded-lg shadow-sm border overflow-hidden">
      <table class="w-full text-sm">
        <thead>
          <tr class="border-b bg-gray-50 text-left">
            <th class="py-3 px-4">{{ $t('page.customers.table_name') }}</th>
            <th class="py-3 px-4">{{ $t('page.customers.phone') }}</th>
            <th class="py-3 px-4">{{ $t('page.customers.address') }}</th>
            <th class="py-3 px-4">{{ $t('page.customers.observations') }}</th>
            <th class="py-3 px-4 w-24"></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="c in customers" :key="c.id" class="border-b hover:bg-gray-50">
            <td class="py-3 px-4 font-medium">{{ c.name }}</td>
            <td class="py-3 px-4 text-gray-600">{{ c.phone || $t('page.customers.empty_placeholder') }}</td>
            <td class="py-3 px-4 text-gray-600 text-xs">
              <div>{{ [c.address_street, c.address_neighborhood, c.address_city].filter(Boolean).join(', ') || $t('page.customers.empty_placeholder') }}</div>
              <div v-if="c.address2_street" class="mt-1 text-gray-400">{{ [c.address2_street, c.address2_neighborhood, c.address2_city].filter(Boolean).join(', ') }}</div>
            </td>
            <td class="py-3 px-4 text-gray-500 text-xs max-w-[200px] truncate">{{ c.notes || $t('page.customers.empty_placeholder') }}</td>
            <td class="py-3 px-4 flex gap-2 items-center">
              <o-button variant="info" size="small" :title="$t('page.customers.edit_title')" @click="openEdit(c)"><i class="mdi mdi-pencil"></i></o-button>
              <o-button variant="danger" size="small" :title="$t('page.customers.delete_title')" @click="deleteCustomer(c)"><i class="mdi mdi-delete"></i></o-button>
            </td>
          </tr>
          <tr v-if="!customers.length">
            <td colspan="5" class="py-8 text-center text-gray-400">{{ $t('page.customers.no_customers') }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <o-modal v-model:active="showModal" :width="500">
      <div class="rounded-lg overflow-hidden">
        <div class="bg-green-700 text-white px-6 py-4 flex items-center justify-between">
          <h3 class="text-lg font-bold">{{ editingId ? $t('page.customers.edit') : $t('page.customers.new') }}</h3>
          <o-button variant="ghost" class="text-white/80 text-xl leading-none" @click="showModal = false">&times;</o-button>
        </div>
        <form @submit.prevent="save" class="p-6 space-y-4">
          <o-field :label="$t('page.customers.table_name')">
            <o-input v-model="form.name" required />
          </o-field>
          <o-field :label="$t('page.customers.phone')">
            <o-input v-model="form.phone" :placeholder="$t('page.customers.phone_placeholder')" />
          </o-field>
          <div class="border rounded-lg p-3 bg-gray-50 space-y-3">
            <p class="text-sm font-semibold text-gray-600">{{ $t('page.customers.address_1') }}</p>
            <o-field :label="$t('page.customers.street')">
              <o-input v-model="form.address_street" />
            </o-field>
            <div class="grid grid-cols-2 gap-4">
              <o-field :label="$t('page.customers.neighborhood')">
                <o-input v-model="form.address_neighborhood" />
              </o-field>
              <o-field :label="$t('page.customers.city')">
                <o-input v-model="form.address_city" />
              </o-field>
            </div>
          </div>
          <div class="border rounded-lg p-3 bg-gray-50 space-y-3">
            <p class="text-sm font-semibold text-gray-600">{{ $t('page.customers.address_2') }} <span class="text-xs font-normal text-gray-400">({{ $t('page.customers.optional') }})</span></p>
            <o-field :label="$t('page.customers.street')">
              <o-input v-model="form.address2_street" />
            </o-field>
            <div class="grid grid-cols-2 gap-4">
              <o-field :label="$t('page.customers.neighborhood')">
                <o-input v-model="form.address2_neighborhood" />
              </o-field>
              <o-field :label="$t('page.customers.city')">
                <o-input v-model="form.address2_city" />
              </o-field>
            </div>
          </div>
          <o-field :label="$t('page.customers.observations')">
            <o-input v-model="form.notes" type="textarea" />
          </o-field>
          <div class="flex justify-end gap-3 pt-2 border-t">
            <o-button type="button" @click="showModal = false">
              {{ $t('page.customers.cancel') }}
            </o-button>
            <o-button variant="primary" type="submit" class="font-semibold py-2 px-6 rounded shadow-sm">
              {{ $t('page.customers.save') }}
            </o-button>
          </div>
        </form>
      </div>
    </o-modal>
  </div>
</template>
