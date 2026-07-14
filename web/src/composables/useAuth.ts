import { useAuthStore } from '@/stores/auth'

export function useAuth() {
  const auth = useAuthStore()

  async function login(username: string, password: string) {
    await auth.login(username, password)
    return '/'
  }

  return { login, logout: auth.logout, user: auth.user, isAuthenticated: auth.isAuthenticated }
}
