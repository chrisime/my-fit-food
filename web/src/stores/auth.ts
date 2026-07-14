import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { post } from '@/composables/api'

interface User {
  id: number
  username: string
  full_name: string
  role: string
}

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || '')
  const user = ref<User | null>(
    JSON.parse(localStorage.getItem('user') || 'null')
  )

  const isAuthenticated = computed(() => !!token.value)

  async function login(username: string, password: string) {
    const data = await post<{ access_token: string; user: User }>('/auth/login', { username, password })
    token.value = data.access_token
    user.value = data.user
    localStorage.setItem('token', data.access_token)
    localStorage.setItem('user', JSON.stringify(data.user))
    localStorage.setItem('role', data.user.role)
  }

  function logout() {
    token.value = ''
    user.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    localStorage.removeItem('role')
    window.location.href = '/login'
  }

  return { token, user, isAuthenticated, login, logout }
})
