<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { listAccounts, createAccount, resetAccount, type Account } from '../api/trading'

const { t, locale } = useI18n()

const accounts = ref<Account[]>([])
const loading = ref(false)

// Create form
const showCreate = ref(false)
const newName = ref('My Sim Account')
const newMarket = ref('a_share')
const creating = ref(false)

const marketKeys = ['a_share', 'us_stock', 'hk_stock', 'fund', 'bond'] as const

async function loadAccounts() {
  loading.value = true
  try {
    accounts.value = await listAccounts()
  } catch {
    accounts.value = []
  } finally {
    loading.value = false
  }
}

async function handleCreate() {
  creating.value = true
  try {
    await createAccount({ name: newName.value, market: newMarket.value, is_simulated: true })
    showCreate.value = false
    await loadAccounts()
  } catch {
    // ignore
  } finally {
    creating.value = false
  }
}

async function handleReset(id: string) {
  if (!confirm(t('accounts.resetConfirm'))) return
  try {
    await resetAccount(id)
    await loadAccounts()
  } catch {
    // ignore
  }
}

function formatDate(iso: string): string {
  const loc = locale.value === 'zh' ? 'zh-CN' : 'en-US'
  return new Date(iso).toLocaleDateString(loc)
}

onMounted(loadAccounts)
</script>

<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold text-gray-900">{{ t('accounts.title') }}</h1>
      <button
        @click="showCreate = !showCreate"
        class="bg-blue-600 text-white px-4 py-1.5 rounded-md text-sm hover:bg-blue-700 transition"
      >
        {{ showCreate ? t('common.cancel') : t('accounts.newAccount') }}
      </button>
    </div>

    <!-- Create form -->
    <div v-if="showCreate" class="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-6">
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div>
          <label class="block text-xs text-gray-500 mb-1">{{ t('common.name') }}</label>
          <input
            v-model="newName"
            class="w-full border border-gray-300 rounded-md px-3 py-1.5 text-sm focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
        <div>
          <label class="block text-xs text-gray-500 mb-1">{{ t('common.market') }}</label>
          <select
            v-model="newMarket"
            class="w-full border border-gray-300 rounded-md px-3 py-1.5 text-sm focus:ring-blue-500 focus:border-blue-500"
          >
            <option v-for="mk in marketKeys" :key="mk" :value="mk">{{ t(`accounts.marketOptions.${mk}`) }}</option>
          </select>
        </div>
        <div class="flex items-end">
          <button
            @click="handleCreate"
            :disabled="creating"
            class="bg-green-600 text-white px-4 py-1.5 rounded-md text-sm hover:bg-green-700 transition disabled:opacity-50"
          >
            {{ creating ? t('accounts.creating') : t('common.create') }}
          </button>
        </div>
      </div>
    </div>

    <!-- Account list -->
    <div v-if="loading" class="text-center py-12 text-gray-500">{{ t('common.loading') }}</div>
    <div v-else-if="accounts.length === 0" class="text-center py-12 text-gray-500">
      {{ t('accounts.noAccounts') }}
    </div>
    <div v-else class="space-y-3">
      <div
        v-for="a in accounts"
        :key="a.id"
        class="bg-white rounded-lg shadow-sm border border-gray-200 p-4 flex items-center justify-between"
      >
        <div>
          <h3 class="text-sm font-bold text-gray-900">{{ a.name }}</h3>
          <div class="flex items-center gap-3 mt-1 text-xs text-gray-500">
            <span class="px-1.5 py-0.5 rounded bg-gray-100">{{ t(`market.${a.market}`) }}</span>
            <span v-if="a.is_simulated" class="px-1.5 py-0.5 rounded bg-yellow-100 text-yellow-700">{{ t('accounts.simulated') }}</span>
            <span>{{ t('accounts.created') }} {{ formatDate(a.created_at) }}</span>
          </div>
        </div>
        <div class="text-right">
          <p class="text-lg font-mono font-bold">¥{{ Number(a.balance).toLocaleString() }}</p>
          <div class="mt-1 flex gap-2">
            <router-link
              :to="'/trading?account=' + a.id"
              class="text-xs text-blue-600 hover:text-blue-800"
            >
              {{ t('accounts.trade') }}
            </router-link>
            <button
              v-if="a.is_simulated"
              @click="handleReset(a.id)"
              class="text-xs text-gray-500 hover:text-red-600"
            >
              {{ t('common.reset') }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
