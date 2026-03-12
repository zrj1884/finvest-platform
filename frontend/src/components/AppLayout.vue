<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const router = useRouter()
const mobileMenuOpen = ref(false)

function handleLogout() {
  auth.logout()
  router.push('/login')
}

onMounted(() => auth.init())

const navItems = [
  { name: 'Dashboard', path: '/' },
  { name: 'A-Share', path: '/market/a_share' },
  { name: 'US Stock', path: '/market/us_stock' },
  { name: 'HK Stock', path: '/market/hk_stock' },
  { name: 'Fund', path: '/fund' },
  { name: 'Bond', path: '/bond' },
  { name: 'News', path: '/news' },
  { name: 'AI Report', path: '/report' },
  { name: 'Sentiment', path: '/sentiment' },
  { name: 'Trading', path: '/trading' },
  { name: 'Portfolio', path: '/portfolio' },
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
                {{ item.name }}
              </router-link>
            </div>
          </div>
          <!-- Auth -->
          <div class="hidden md:flex items-center gap-3 ml-4">
            <template v-if="auth.isLoggedIn">
              <span class="text-sm text-gray-500">{{ auth.user?.nickname || auth.user?.email }}</span>
              <button
                @click="handleLogout"
                class="text-sm text-gray-500 hover:text-red-600"
              >Logout</button>
            </template>
            <router-link v-else to="/login" class="text-sm text-blue-600 hover:text-blue-800">Sign In</router-link>
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
            {{ item.name }}
          </router-link>
        </div>
      </div>
    </nav>

    <!-- Main content -->
    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      <router-view />
    </main>
  </div>
</template>
