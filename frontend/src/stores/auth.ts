import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  login as apiLogin,
  register as apiRegister,
  refreshToken as apiRefresh,
  getMe,
  type UserInfo,
} from '../api/auth'

// Access token lifetime in ms (match backend: 30 min, refresh 5 min early)
const ACCESS_TOKEN_LIFETIME_MS = 25 * 60 * 1000

export const useAuthStore = defineStore('auth', () => {
  const user = ref<UserInfo | null>(null)
  const token = ref(localStorage.getItem('access_token') || '')
  const tokenExpiresAt = ref(Number(localStorage.getItem('token_expires_at') || '0'))

  const isLoggedIn = computed(() => !!token.value && !isTokenExpired())

  function isTokenExpired(): boolean {
    if (!tokenExpiresAt.value) return true
    return Date.now() > tokenExpiresAt.value
  }

  function saveTokens(accessToken: string, refreshTokenVal: string) {
    const expiresAt = Date.now() + ACCESS_TOKEN_LIFETIME_MS
    token.value = accessToken
    tokenExpiresAt.value = expiresAt
    localStorage.setItem('access_token', accessToken)
    localStorage.setItem('refresh_token', refreshTokenVal)
    localStorage.setItem('token_expires_at', String(expiresAt))
  }

  async function login(email: string, password: string) {
    const resp = await apiLogin({ email, password })
    saveTokens(resp.access_token, resp.refresh_token)
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

  /** Try to refresh access token using stored refresh token. Returns true on success. */
  async function tryRefresh(): Promise<boolean> {
    const rt = localStorage.getItem('refresh_token')
    if (!rt) return false
    try {
      const resp = await apiRefresh(rt)
      saveTokens(resp.access_token, resp.refresh_token)
      return true
    } catch {
      logout()
      return false
    }
  }

  function logout() {
    token.value = ''
    tokenExpiresAt.value = 0
    user.value = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('token_expires_at')
  }

  // Restore session on store creation
  async function init() {
    if (!token.value) return

    if (isTokenExpired()) {
      // Access token expired, try refresh
      const ok = await tryRefresh()
      if (!ok) return
    }

    await fetchUser()
    if (!user.value) {
      // Token invalid, try refresh once
      const ok = await tryRefresh()
      if (ok) await fetchUser()
      if (!user.value) logout()
    }
  }

  return { user, token, isLoggedIn, login, registerAndLogin, fetchUser, tryRefresh, logout, init }
})
