<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { listAccounts, type Account } from '../api/trading'
import OrderPanel from '../components/OrderPanel.vue'
import OrderList from '../components/OrderList.vue'
import PositionTable from '../components/PositionTable.vue'

const { t } = useI18n()

const accounts = ref<Account[]>([])
const selectedAccountId = ref('')
const loading = ref(false)

const selectedAccount = computed(() => accounts.value.find((a) => a.id === selectedAccountId.value))

const orderListRef = ref<InstanceType<typeof OrderList>>()
const positionRef = ref<InstanceType<typeof PositionTable>>()

async function loadAccounts() {
  loading.value = true
  try {
    accounts.value = await listAccounts()
    const first = accounts.value[0]
    if (first && !selectedAccountId.value) {
      selectedAccountId.value = first.id
    }
  } catch {
    accounts.value = []
  } finally {
    loading.value = false
  }
}

function onOrderPlaced() {
  orderListRef.value?.refresh()
  positionRef.value?.refresh()
  loadAccounts()
}

onMounted(loadAccounts)
</script>

<template>
  <div>
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-4 gap-3">
      <h1 class="text-2xl font-bold text-gray-900">{{ t('trading.title') }}</h1>
      <div class="flex items-center gap-3">
        <select
          v-model="selectedAccountId"
          class="border border-gray-300 rounded-md px-3 py-1.5 text-sm focus:ring-blue-500 focus:border-blue-500"
        >
          <option v-for="a in accounts" :key="a.id" :value="a.id">
            {{ a.name }} ({{ t(`market.${a.market}`) }})
          </option>
        </select>
        <router-link
          to="/accounts"
          class="text-sm text-blue-600 hover:text-blue-800 whitespace-nowrap"
        >
          {{ t('trading.manageAccounts') }}
        </router-link>
      </div>
    </div>

    <div v-if="loading" class="text-center py-12 text-gray-500">{{ t('common.loading') }}</div>

    <div v-else-if="accounts.length === 0" class="text-center py-12">
      <p class="text-gray-500 mb-4">{{ t('trading.noAccounts') }}</p>
      <router-link
        to="/accounts"
        class="bg-blue-600 text-white px-4 py-2 rounded-md text-sm hover:bg-blue-700 transition"
      >
        {{ t('trading.createAccount') }}
      </router-link>
    </div>

    <div v-else class="grid grid-cols-1 lg:grid-cols-4 gap-4">
      <div class="lg:col-span-1">
        <OrderPanel
          :account-id="selectedAccountId"
          :market="selectedAccount?.market || ''"
          @order-placed="onOrderPlaced"
        />
      </div>
      <div class="lg:col-span-3 space-y-4">
        <PositionTable ref="positionRef" :account-id="selectedAccountId" />
        <OrderList ref="orderListRef" :account-id="selectedAccountId" />
      </div>
    </div>
  </div>
</template>
