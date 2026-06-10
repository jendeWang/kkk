import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth.js'
import Layout from '../views/Layout.vue'

const routes = [
  { path: '/login', name: 'Login', component: () => import('../views/Login.vue'), meta: { requiresAuth: false } },
  { path: '/', redirect: '/dashboard' },
  {
    path: '/',
    component: Layout,
    meta: { requiresAuth: true },
    children: [
      { path: 'dashboard', name: 'Dashboard', component: () => import('../views/Dashboard.vue') },
      { path: 'products', name: 'Products', component: () => import('../views/Products.vue') },
      { path: 'devices', name: 'Devices', component: () => import('../views/Devices.vue') },
      { path: 'telemetry', name: 'Telemetry', component: () => import('../views/Telemetry.vue') },
      { path: 'commands', name: 'Commands', component: () => import('../views/Commands.vue') },
      { path: 'alert-rules', name: 'AlertRules', component: () => import('../views/AlertRules.vue') },
      { path: 'alerts', name: 'Alerts', component: () => import('../views/Alerts.vue') },
      { path: 'api-keys', name: 'APIKeys', component: () => import('../views/APIKeys.vue') },
    ]
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  if (to.meta.requiresAuth && !authStore.token) {
    next('/login')
  } else if (to.path === '/login' && authStore.token) {
    next('/dashboard')
  } else {
    next()
  }
})

export default router
