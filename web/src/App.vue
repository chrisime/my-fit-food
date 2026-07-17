<script setup lang="ts">
import { useAuthStore } from '@/stores/auth'
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import LanguageSwitcher from '@/components/LanguageSwitcher.vue'

const auth = useAuthStore()
const router = useRouter()

onMounted(() => {
  if (!auth.isAuthenticated) {
    if (router.currentRoute.value.name !== 'login') router.push('/login')
  }
})
</script>

<template>
  <div class="min-h-screen bg-gray-50">
    <nav v-if="auth.isAuthenticated" class="bg-green-700 text-white px-6 py-3 flex items-center gap-6">
      <div class="flex-1 flex items-center gap-4">
        <div class="font-bold text-lg">{{ $t('nav.brand') }}</div>
        <router-link to="/" class="px-3 py-1.5 rounded hover:bg-green-600 font-medium text-sm">{{ $t('nav.dashboard') }}</router-link>
        <div class="flex items-center gap-1 text-sm">
          <router-link to="/sales" class="px-3 py-1.5 rounded hover:bg-green-600 font-medium" v-if="auth.user?.role === 'sales' || auth.user?.role === 'admin'">{{ $t('nav.sales') }}</router-link>
          <span v-if="auth.user?.role === 'sales' || auth.user?.role === 'admin'" class="text-green-300">|</span>
          <router-link to="/customers" class="px-3 py-1.5 rounded hover:bg-green-600 font-medium" v-if="auth.user?.role === 'sales' || auth.user?.role === 'admin'">{{ $t('nav.customers') }}</router-link>
          <span v-if="auth.user?.role === 'sales' || auth.user?.role === 'admin'" class="text-green-300">|</span>
          <router-link to="/products" class="px-3 py-1.5 rounded hover:bg-green-600 font-medium" v-if="auth.user?.role === 'admin' || auth.user?.role === 'sales'">{{ $t('nav.products') }}</router-link>
        </div>
        <div class="flex items-center gap-1 text-sm">
          <router-link to="/kitchen" class="px-3 py-1.5 rounded hover:bg-green-600 font-medium" v-if="auth.user?.role === 'kitchen' || auth.user?.role === 'admin'">{{ $t('nav.kitchen') }}</router-link>
          <span v-if="auth.user?.role === 'kitchen' || auth.user?.role === 'admin'" class="text-green-300">|</span>
          <router-link to="/stock" class="px-3 py-1.5 rounded hover:bg-green-600 font-medium">{{ $t('nav.stock') }}</router-link>
        </div>
        <router-link to="/dispatch" class="px-3 py-1.5 rounded hover:bg-green-600 font-medium text-sm" v-if="auth.user?.role === 'admin'">{{ $t('nav.dispatch') }}</router-link>
      </div>

      <div class="text-sm justify-end">
        {{ $t('nav.logged_as') }} <strong>{{ auth.user?.full_name }}</strong>
      </div>

      <div class="flex items-center justify-end gap-4">
        <router-link to="/users" class="hover:text-green-200" :title="$t('nav.users')" v-if="auth.user?.role === 'admin'"><i class="fas fa-user-cog text-xl"></i></router-link>
        <LanguageSwitcher />
        <o-button variant="ghost" class="text-white" :title="$t('nav.logout')" @click="auth.logout()"><i class="fas fa-sign-out-alt text-xl"></i></o-button>
      </div>
    </nav>
    <main class="p-6">
      <router-view />
    </main>
  </div>
</template>
