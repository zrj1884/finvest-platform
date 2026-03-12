import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login as apiLogin, register as apiRegister, getMe, type UserInfo } from '../api/auth'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<UserInfo | null>(null)
  const token = ref(localStorage.getItem('access_token') || '')

  const isLoggedIn = computed(() => !!token.value)

  async function login(email: string, password: string) {
    const resp = await apiLogin({ email, password })
    token.value = resp.access_token
    localStorage.setItem('access_token', resp.access_token)
    localStorage.setItem('refresh_token', resp.refresh_token)
    await fetchUser()
  }

  async function registerAndLogin(email: string, password: string, nickname?: string) {
    await apiRegister({ email, password, nickname })
    await login(email, password)
  }

  async function fetchUser() {
    try {
      user.value = await getMe()
    } catch {
      user.value = null
    }
  }

  function logout() {
    token.value = ''
    user.value = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
  }

  // Try to restore session on store creation
  async function init() {
    if (token.value) {
      await fetchUser()
      if (!user.value) {
        // Token expired or invalid
        logout()
      }
    }
  }

  return { user, token, isLoggedIn, login, registerAndLogin, fetchUser, logout, init }
})
