import { createApp } from 'vue'
import './style.css'
import App from './App.vue'
import router from './router'
import pinia from './stores'
import i18n from './i18n'

import { useAuthStore } from './stores/auth'

const app = createApp(App)
app.use(pinia)
app.use(router)
app.use(i18n)

// Restore login session before mounting
const auth = useAuthStore()
auth.init().finally(() => {
  app.mount('#app')
})
