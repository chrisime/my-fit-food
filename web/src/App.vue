<script setup lang="ts">
import { useAuthStore } from '@/stores/auth'
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'

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
        <div class="font-bold text-lg">My Fit Food</div>
        <router-link to="/" class="px-3 py-1.5 rounded hover:bg-green-600 font-medium text-sm">Dashboard</router-link>
        <div class="flex items-center gap-1 text-sm">
          <router-link to="/vendas" class="px-3 py-1.5 rounded hover:bg-green-600 font-medium" v-if="auth.user?.role === 'vendas' || auth.user?.role === 'admin'">Vendas</router-link>
          <span v-if="auth.user?.role === 'vendas' || auth.user?.role === 'admin'" class="text-green-300">|</span>
          <router-link to="/clientes" class="px-3 py-1.5 rounded hover:bg-green-600 font-medium" v-if="auth.user?.role === 'vendas' || auth.user?.role === 'admin'">Clientes</router-link>
          <span v-if="auth.user?.role === 'vendas' || auth.user?.role === 'admin'" class="text-green-300">|</span>
          <router-link to="/produtos" class="px-3 py-1.5 rounded hover:bg-green-600 font-medium" v-if="auth.user?.role === 'admin' || auth.user?.role === 'vendas'">Produtos</router-link>
        </div>
        <div class="flex items-center gap-1 text-sm">
          <router-link to="/cozinha" class="px-3 py-1.5 rounded hover:bg-green-600 font-medium" v-if="auth.user?.role === 'cozinha' || auth.user?.role === 'admin'">Cozinha</router-link>
          <span v-if="auth.user?.role === 'cozinha' || auth.user?.role === 'admin'" class="text-green-300">|</span>
          <router-link to="/estoque" class="px-3 py-1.5 rounded hover:bg-green-600 font-medium">Estoque</router-link>
        </div>
        <router-link to="/expedicao" class="px-3 py-1.5 rounded hover:bg-green-600 font-medium text-sm" v-if="auth.user?.role === 'admin'">Expedição</router-link>
      </div>

      <div class="text-sm text-center">
        Logado como <strong>{{ auth.user?.full_name }}</strong>
      </div>

      <div class="flex-1 flex items-center justify-end gap-4">
        <router-link to="/usuarios" class="hover:text-green-200" title="Usuários" v-if="auth.user?.role === 'admin'"><i class="mdi mdi-account-cog text-xl"></i></router-link>
        <button class="hover:text-green-200" title="Sair" @click="auth.logout()"><i class="mdi mdi-logout-variant text-xl"></i></button>
      </div>
    </nav>
    <main class="p-6">
      <router-view />
    </main>
  </div>
</template>
