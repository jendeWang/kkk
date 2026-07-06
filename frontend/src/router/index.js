import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth.js'
import Layout from '../views/Layout.vue'

const routes = [
  { path: '/login', name: 'Login', component: () => import('../views/Login.vue'), meta: { requiresAuth: false } },
  { path: '/register', name: 'Register', component: () => import('../views/Register.vue'), meta: { requiresAuth: false } },
  { path: '/big-screen', name: 'BigScreen', component: () => import('../views/BigScreen.vue'), meta: { requiresAuth: true } },
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
      { path: 'sensors', name: 'Sensors', component: () => import('../views/Sensors.vue') },
      { path: 'commands', name: 'Commands', component: () => import('../views/Commands.vue') },
      { path: 'alert-rules', name: 'AlertRules', component: () => import('../views/AlertRules.vue') },
      { path: 'alerts', name: 'Alerts', component: () => import('../views/Alerts.vue') },
      { path: 'scenes', name: 'Scenes', component: () => import('../views/Scenes.vue') },
      { path: 'groups', name: 'Groups', component: () => import('../views/Groups.vue') },
      { path: 'api-keys', name: 'APIKeys', component: () => import('../views/APIKeys.vue') },
      { path: 'api-playground', name: 'APIPlayground', component: () => import('../views/APIPlayground.vue'), meta: { requiresAuth: true } },
      { path: 'topology', name: 'Topology', component: () => import('../views/Topology.vue') },
      { path: 'operation-logs', name: 'OperationLogs', component: () => import('../views/OperationLogs.vue') },
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
  } else if ((to.path === '/login' || to.path === '/register') && authStore.token) {
    next('/dashboard')
  } else {
    next()
  }
})

export default router
