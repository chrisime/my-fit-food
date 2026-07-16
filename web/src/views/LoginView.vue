<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '@/composables/useAuth'
import { useToast } from '@/composables/useToast'

const router = useRouter()
const { login } = useAuth()
const { toastError } = useToast()
const username = ref('')
const password = ref('')
const loading = ref(false)

async function handleLogin() {
  loading.value = true
  try {
    const path = await login(username.value, password.value)
    router.push(path)
  } catch (e) {
    toastError(e)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="flex items-center justify-center min-h-[80vh]">
    <div class="bg-white p-8 rounded-lg shadow-md w-full max-w-sm">
      <h1 class="text-2xl font-bold text-green-700 mb-6 text-center">{{ $t('page.login.title') }}</h1>
      <form class="space-y-4" @submit.prevent="handleLogin">
        <o-field :label="$t('page.login.username')">
          <o-input v-model="username" expanded required />
        </o-field>
        <o-field :label="$t('page.login.password')">
          <o-input v-model="password" type="password" expanded required password-reveal />
        </o-field>
        <button
          type="submit"
          :disabled="loading"
          class="w-full bg-green-600 hover:bg-green-700 text-white font-semibold py-2 px-4 rounded disabled:opacity-50"
        >
          {{ loading ? $t('page.login.entering') : $t('page.login.enter') }}
        </button>
      </form>
    </div>
  </div>
</template>
