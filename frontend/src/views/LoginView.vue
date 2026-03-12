<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '../stores/auth'

const { t } = useI18n()
const auth = useAuthStore()
const router = useRouter()

const isRegister = ref(false)
const email = ref('')
const password = ref('')
const nickname = ref('')
const error = ref('')
const loading = ref(false)

async function handleSubmit() {
  error.value = ''
  loading.value = true
  try {
    if (isRegister.value) {
      await auth.registerAndLogin(email.value, password.value, nickname.value || undefined)
    } else {
      await auth.login(email.value, password.value)
    }
    const redirect = (router.currentRoute.value.query.redirect as string) || '/'
    router.push(redirect)
  } catch (e: unknown) {
    if (e && typeof e === 'object' && 'response' in e) {
      const resp = (e as { response: { data: { detail: string } } }).response
      error.value = resp?.data?.detail || t('login.requestFailed')
    } else {
      error.value = t('login.networkError')
    }
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="min-h-screen bg-gray-50 flex items-center justify-center px-4">
    <div class="max-w-sm w-full">
      <h1 class="text-3xl font-bold text-blue-600 text-center mb-2">{{ t('login.title') }}</h1>
      <p class="text-center text-gray-500 text-sm mb-6">
        {{ isRegister ? t('login.createAccount') : t('login.signIn') }}
      </p>

      <form @submit.prevent="handleSubmit" class="bg-white rounded-lg shadow p-6 space-y-4">
        <div v-if="error" class="text-red-600 text-sm bg-red-50 px-3 py-2 rounded">{{ error }}</div>

        <div v-if="isRegister">
          <label class="block text-xs text-gray-500 mb-1">{{ t('login.nickname') }}</label>
          <input
            v-model="nickname"
            type="text"
            class="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:ring-blue-500 focus:border-blue-500"
            :placeholder="t('login.nicknamePlaceholder')"
          />
        </div>
        <div>
          <label class="block text-xs text-gray-500 mb-1">{{ t('login.email') }}</label>
          <input
            v-model="email"
            type="email"
            required
            class="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:ring-blue-500 focus:border-blue-500"
            :placeholder="t('login.emailPlaceholder')"
          />
        </div>
        <div>
          <label class="block text-xs text-gray-500 mb-1">{{ t('login.password') }}</label>
          <input
            v-model="password"
            type="password"
            required
            minlength="6"
            class="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:ring-blue-500 focus:border-blue-500"
            :placeholder="t('login.passwordPlaceholder')"
          />
        </div>
        <button
          type="submit"
          :disabled="loading"
          class="w-full bg-blue-600 text-white py-2 rounded-md text-sm font-medium hover:bg-blue-700 transition disabled:opacity-50"
        >
          {{ loading ? t('login.waiting') : isRegister ? t('login.register') : t('login.submit') }}
        </button>
      </form>

      <p class="text-center text-sm text-gray-500 mt-4">
        <button @click="isRegister = !isRegister" class="text-blue-600 hover:text-blue-800">
          {{ isRegister ? t('login.switchToLogin') : t('login.switchToRegister') }}
        </button>
      </p>
    </div>
  </div>
</template>
