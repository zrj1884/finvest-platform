import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Attach JWT token if available
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Auto-refresh on 401 response
let refreshing: Promise<boolean> | null = null

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config
    if (
      error.response?.status === 401 &&
      !original._retry &&
      !original.url?.includes('/auth/')
    ) {
      original._retry = true

      // Deduplicate concurrent refresh attempts
      if (!refreshing) {
        refreshing = (async () => {
          const rt = localStorage.getItem('refresh_token')
          if (!rt) return false
          try {
            const resp = await axios.post('/api/v1/auth/refresh', { refresh_token: rt })
            const { access_token, refresh_token } = resp.data
            const expiresAt = Date.now() + 25 * 60 * 1000
            localStorage.setItem('access_token', access_token)
            localStorage.setItem('refresh_token', refresh_token)
            localStorage.setItem('token_expires_at', String(expiresAt))
            return true
          } catch {
            localStorage.removeItem('access_token')
            localStorage.removeItem('refresh_token')
            localStorage.removeItem('token_expires_at')
            return false
          } finally {
            refreshing = null
          }
        })()
      }

      const ok = await refreshing
      if (ok) {
        original.headers.Authorization = `Bearer ${localStorage.getItem('access_token')}`
        return api(original)
      }
    }
    return Promise.reject(error)
  },
)

export default api
