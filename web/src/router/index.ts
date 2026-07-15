import { createRouter, createWebHistory } from 'vue-router'
import LoginView from '@/views/LoginView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', name: 'login', component: LoginView },
    {
      path: '/clientes',
      name: 'clientes',
      component: () => import('@/views/ClientesView.vue'),
      meta: { roles: ['vendas', 'admin'] },
    },
    {
      path: '/vendas',
      name: 'vendas',
      component: () => import('@/views/VendasView.vue'),
      meta: { roles: ['vendas', 'admin'] },
    },
    {
      path: '/cozinha',
      name: 'cozinha',
      component: () => import('@/views/CozinhaView.vue'),
      meta: { roles: ['cozinha', 'admin'] },
    },
    {
      path: '/expedicao',
      name: 'expedicao',
      component: () => import('@/views/ExpedicaoView.vue'),
      meta: { roles: ['admin'] },
    },
    {
      path: '/produtos',
      name: 'produtos',
      component: () => import('@/views/ProdutosView.vue'),
      meta: { roles: ['admin', 'vendas'] },
    },
    {
      path: '/estoque',
      name: 'estoque',
      component: () => import('@/views/StockView.vue'),
      meta: { roles: ['vendas', 'cozinha', 'admin'] },
    },
    {
      path: '/usuarios',
      name: 'usuarios',
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
