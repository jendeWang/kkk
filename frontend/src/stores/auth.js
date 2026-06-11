import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '../services/api.js'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || '')
  const user = ref(null)

  const isLoggedIn = computed(() => !!token.value)

  async function login(username, password) {
    const response = await api.post('/auth/login', { username, password })
    token.value = response.data.access_token
    localStorage.setItem('token', token.value)
    await fetchUser()
    return response.data
  }

  async function register(username, password, email, full_name) {
    const response = await api.post('/auth/register', { username, password, email, full_name })
    token.value = response.data.access_token
    localStorage.setItem('token', token.value)
    await fetchUser()
    return response.data
  }

  function logout() {
    token.value = ''
    user.value = null
    localStorage.removeItem('token')
  }

  async function fetchUser() {
    try {
      const response = await api.get('/auth/me')
      user.value = response.data
    } catch (error) {
      logout()
      throw error
    }
  }

  return { token, user, isLoggedIn, login, register, logout, fetchUser }
})
