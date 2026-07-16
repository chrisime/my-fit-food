import { createRouter, createWebHistory } from 'vue-router'
import LoginView from '@/views/LoginView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', name: 'login', component: LoginView },
    {
      path: '/customers',
      name: 'customers',
      component: () => import('@/views/ClientesView.vue'),
      meta: { roles: ['sales', 'admin'] },
    },
    {
      path: '/sales',
      name: 'sales',
      component: () => import('@/views/VendasView.vue'),
      meta: { roles: ['sales', 'admin'] },
    },
    {
      path: '/kitchen',
      name: 'kitchen',
      component: () => import('@/views/CozinhaView.vue'),
      meta: { roles: ['kitchen', 'admin'] },
    },
    {
      path: '/dispatch',
      name: 'dispatch',
      component: () => import('@/views/ExpedicaoView.vue'),
      meta: { roles: ['admin'] },
    },
    {
      path: '/products',
      name: 'products',
      component: () => import('@/views/ProdutosView.vue'),
      meta: { roles: ['admin', 'sales'] },
    },
    {
      path: '/stock',
      name: 'stock',
      component: () => import('@/views/StockView.vue'),
      meta: { roles: ['sales', 'kitchen', 'admin'] },
    },
    {
      path: '/users',
      name: 'users',
      component: () => import('@/views/UsuariosView.vue'),
      meta: { roles: ['admin'] },
    },
    {
      path: '/',
      name: 'dashboard',
      component: () => import('@/views/DashboardView.vue'),
    },
    { path: '/:pathMatch(.*)*', redirect: '/' },
  ],
})

router.beforeEach((to, _from) => {
  const token = localStorage.getItem('token')
  const role = localStorage.getItem('role')
  if (to.name !== 'login' && !token) return '/login'
  if (to.meta.roles && role && !(to.meta.roles as string[]).includes(role)) {
    return '/login'
  }
})

export default router
