<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getFundNav, type FundNav } from '../api/market'

const router = useRouter()
const funds = ref<FundNav[]>([])
const loading = ref(false)
const searchSymbol = ref('')

const defaultFunds = ['110011', '163402', '000961', '001156', '005827']

async function loadData() {
  loading.value = true
  funds.value = []
  try {
    const results = await Promise.all(
      defaultFunds.map((s) => getFundNav(s, 1).catch(() => [] as FundNav[])),
    )
    funds.value = results.flat()
  } catch {
    // ignore
  } finally {
    loading.value = false
  }
}

function searchFund() {
  if (searchSymbol.value.trim()) {
    router.push(`/fund/${searchSymbol.value.trim()}`)
  }
}

onMounted(loadData)
</script>

<template>
  <div>
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6">
      <h1 class="text-2xl font-bold text-gray-900">Funds</h1>
      <div class="mt-3 sm:mt-0 flex gap-2">
        <input
          v-model="searchSymbol"
          @keyup.enter="searchFund"
          type="text"
          placeholder="Enter fund code..."
          class="border border-gray-300 rounded-md px-3 py-1.5 text-sm focus:ring-blue-500 focus:border-blue-500"
        />
        <button
          @click="searchFund"
          class="bg-blue-600 text-white px-4 py-1.5 rounded-md text-sm hover:bg-blue-700 transition"
        >
          Search
        </button>
      </div>
    </div>

    <div v-if="loading" class="text-center py-12 text-gray-500">Loading...</div>
    <div v-else-if="funds.length === 0" class="text-center py-12 text-gray-500">
      No fund data available.
    </div>
    <div v-else class="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
      <div class="overflow-x-auto">
        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-50">
            <tr>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Code</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Name</th>
              <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">NAV</th>
              <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Acc. NAV</th>
              <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Daily Return</th>
              <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Date</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-200">
            <tr v-for="fund in funds" :key="fund.symbol" class="hover:bg-gray-50">
              <td class="px-4 py-3 text-sm font-medium text-blue-600">{{ fund.symbol }}</td>
              <td class="px-4 py-3 text-sm text-gray-700">{{ fund.name || '-' }}</td>
              <td class="px-4 py-3 text-sm text-right font-mono">{{ fund.nav.toFixed(4) }}</td>
              <td class="px-4 py-3 text-sm text-right font-mono">
                {{ fund.accumulated_nav?.toFixed(4) || '-' }}
              </td>
              <td
                class="px-4 py-3 text-sm text-right font-mono"
                :class="fund.daily_return != null && fund.daily_return >= 0 ? 'text-red-600' : 'text-green-600'"
              >
                {{ fund.daily_return != null ? fund.daily_return.toFixed(2) + '%' : '-' }}
              </td>
              <td class="px-4 py-3 text-sm text-right text-gray-500">
                {{ fund.time.split('T')[0] }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
