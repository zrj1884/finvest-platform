<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '../stores/auth'
import { setLocale } from '../i18n'

const { t, locale } = useI18n()
const auth = useAuthStore()
const router = useRouter()
const mobileMenuOpen = ref(false)

function handleLogout() {
  auth.logout()
  router.push('/login')
}

function toggleLocale() {
  const next = locale.value === 'zh' ? 'en' : 'zh'
  setLocale(next)
}

const navItems = [
  { key: 'nav.dashboard', path: '/' },
  { key: 'nav.aShare', path: '/market/a_share' },
  { key: 'nav.usStock', path: '/market/us_stock' },
  { key: 'nav.hkStock', path: '/market/hk_stock' },
  { key: 'nav.fund', path: '/fund' },
  { key: 'nav.bond', path: '/bond' },
  { key: 'nav.news', path: '/news' },
  { key: 'nav.aiReport', path: '/report' },
  { key: 'nav.sentiment', path: '/sentiment' },
  { key: 'nav.trading', path: '/trading' },
  { key: 'nav.portfolio', path: '/portfolio' },
]
</script>

<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Top navigation bar -->
    <nav class="bg-white shadow-sm border-b border-gray-200">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between h-14">
          <div class="flex items-center">
            <router-link to="/" class="text-xl font-bold text-blue-600">FinVest</router-link>
            <!-- Desktop nav -->
            <div class="hidden md:flex ml-8 space-x-1">
              <router-link
                v-for="item in navItems"
                :key="item.path"
                :to="item.path"
                class="px-3 py-2 text-sm font-medium text-gray-600 hover:text-blue-600 hover:bg-blue-50 rounded-md transition"
                active-class="text-blue-600 bg-blue-50"
              >
                {{ t(item.key) }}
              </router-link>
            </div>
          </div>
          <!-- Auth + Lang -->
          <div class="hidden md:flex items-center gap-3 ml-4">
            <button
              @click="toggleLocale"
              class="text-sm text-gray-400 hover:text-blue-600 border border-gray-200 rounded px-1.5 py-0.5"
              :title="locale === 'zh' ? 'Switch to English' : '切换中文'"
            >
              {{ locale === 'zh' ? 'EN' : '中' }}
            </button>
            <template v-if="auth.isLoggedIn">
              <span class="text-sm text-gray-500">{{ auth.user?.nickname || auth.user?.email }}</span>
              <button
                @click="handleLogout"
                class="text-sm text-gray-500 hover:text-red-600"
              >{{ t('nav.logout') }}</button>
            </template>
            <router-link v-else to="/login" class="text-sm text-blue-600 hover:text-blue-800">{{ t('nav.signIn') }}</router-link>
          </div>
          <!-- Mobile menu button -->
          <div class="flex items-center md:hidden">
            <button
              @click="mobileMenuOpen = !mobileMenuOpen"
              class="p-2 rounded-md text-gray-500 hover:text-gray-700 hover:bg-gray-100"
            >
              <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path
                  v-if="!mobileMenuOpen"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M4 6h16M4 12h16M4 18h16"
                />
                <path
                  v-else
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>
        </div>
      </div>
      <!-- Mobile menu -->
      <div v-if="mobileMenuOpen" class="md:hidden border-t border-gray-200">
        <div class="px-2 pt-2 pb-3 space-y-1">
          <router-link
            v-for="item in navItems"
            :key="item.path"
            :to="item.path"
            class="block px-3 py-2 text-sm font-medium text-gray-600 hover:text-blue-600 hover:bg-blue-50 rounded-md"
            active-class="text-blue-600 bg-blue-50"
            @click="mobileMenuOpen = false"
          >
            {{ t(item.key) }}
          </router-link>
          <!-- Mobile: lang + auth -->
          <div class="flex items-center gap-3 px-3 py-2 border-t border-gray-100 mt-2 pt-3">
            <button @click="toggleLocale" class="text-sm text-gray-400 hover:text-blue-600 border border-gray-200 rounded px-1.5 py-0.5">
              {{ locale === 'zh' ? 'EN' : '中' }}
            </button>
            <template v-if="auth.isLoggedIn">
              <span class="text-sm text-gray-500">{{ auth.user?.nickname || auth.user?.email }}</span>
              <button @click="handleLogout" class="text-sm text-gray-500 hover:text-red-600">{{ t('nav.logout') }}</button>
            </template>
            <router-link v-else to="/login" class="text-sm text-blue-600 hover:text-blue-800" @click="mobileMenuOpen = false">{{ t('nav.signIn') }}</router-link>
          </div>
        </div>
      </div>
    </nav>

    <!-- Main content -->
    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      <router-view />
    </main>
  </div>
</template>
