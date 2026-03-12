<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getStockDaily, type StockDaily } from '../api/market'

const route = useRoute()
const router = useRouter()

const market = computed(() => (route.params.market as string) || 'a_share')
const stocks = ref<StockDaily[]>([])
const loading = ref(false)
const searchSymbol = ref('')

const marketLabels: Record<string, string> = {
  a_share: 'A-Share Market',
  us_stock: 'US Stock Market',
  hk_stock: 'HK Stock Market',
}

// Default symbols per market
const defaultSymbols: Record<string, string[]> = {
  a_share: ['000001', '600519', '000858', '601318', '600036'],
  us_stock: ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA'],
  hk_stock: ['00700', '09988', '01810'],
}

async function loadData() {
  loading.value = true
  stocks.value = []
  const symbols = defaultSymbols[market.value] || []

  try {
    const results = await Promise.all(
      symbols.map((s) => getStockDaily(s, market.value, 1).catch(() => [] as StockDaily[])),
    )
    stocks.value = results.flat()
  } catch {
    // ignore
  } finally {
    loading.value = false
  }
}

function goToDetail(symbol: string) {
  router.push(`/stock/${market.value}/${symbol}`)
}

function searchStock() {
  if (searchSymbol.value.trim()) {
    goToDetail(searchSymbol.value.trim())
  }
}

onMounted(loadData)
watch(market, loadData)
</script>

<template>
  <div>
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6">
      <h1 class="text-2xl font-bold text-gray-900">{{ marketLabels[market] || market }}</h1>
      <div class="mt-3 sm:mt-0 flex gap-2">
        <input
          v-model="searchSymbol"
          @keyup.enter="searchStock"
          type="text"
          placeholder="Enter symbol..."
          class="border border-gray-300 rounded-md px-3 py-1.5 text-sm focus:ring-blue-500 focus:border-blue-500"
        />
        <button
          @click="searchStock"
          class="bg-blue-600 text-white px-4 py-1.5 rounded-md text-sm hover:bg-blue-700 transition"
        >
          Search
        </button>
      </div>
    </div>

    <div v-if="loading" class="text-center py-12 text-gray-500">Loading...</div>

    <div v-else-if="stocks.length === 0" class="text-center py-12 text-gray-500">
      No data available. Data will appear after collection runs.
    </div>

    <div v-else class="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
      <div class="overflow-x-auto">
        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-50">
            <tr>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Symbol</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Name</th>
              <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Close</th>
              <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Change %</th>
              <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Volume</th>
              <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Date</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-200">
            <tr
              v-for="stock in stocks"
              :key="stock.symbol"
              @click="goToDetail(stock.symbol)"
              class="hover:bg-gray-50 cursor-pointer transition"
            >
              <td class="px-4 py-3 text-sm font-medium text-blue-600">{{ stock.symbol }}</td>
              <td class="px-4 py-3 text-sm text-gray-700">{{ stock.name || '-' }}</td>
              <td class="px-4 py-3 text-sm text-right font-mono">{{ stock.close.toFixed(2) }}</td>
              <td
                class="px-4 py-3 text-sm text-right font-mono"
                :class="stock.change_pct != null && stock.change_pct >= 0 ? 'text-red-600' : 'text-green-600'"
              >
                {{ stock.change_pct != null ? stock.change_pct.toFixed(2) + '%' : '-' }}
              </td>
              <td class="px-4 py-3 text-sm text-right font-mono">
                {{ stock.volume.toLocaleString() }}
              </td>
              <td class="px-4 py-3 text-sm text-right text-gray-500">
                {{ stock.time.split('T')[0] }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
