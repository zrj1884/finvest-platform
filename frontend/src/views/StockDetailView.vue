<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import KlineChart from '../components/KlineChart.vue'
import RelatedNews from '../components/RelatedNews.vue'
import { getStockKline, getStockDaily, type KlineData, type StockDaily } from '../api/market'
import { generateStockReport, type ReportResponse } from '../api/ai'

const route = useRoute()
const market = computed(() => route.params.market as string)
const symbol = computed(() => route.params.symbol as string)

const klineData = ref<KlineData[]>([])
const latestData = ref<StockDaily | null>(null)
const period = ref('daily')
const loading = ref(false)

async function loadData() {
  loading.value = true
  try {
    const [kline, daily] = await Promise.all([
      getStockKline(symbol.value, market.value, period.value, 300),
      getStockDaily(symbol.value, market.value, 1),
    ])
    klineData.value = kline
    latestData.value = daily[0] ?? null
  } catch {
    // ignore
  } finally {
    loading.value = false
  }
}

const aiReport = ref<ReportResponse | null>(null)
const aiLoading = ref(false)

async function generateReport() {
  aiLoading.value = true
  try {
    aiReport.value = await generateStockReport(symbol.value, market.value)
  } catch {
    // ignore — likely no API key configured
  } finally {
    aiLoading.value = false
  }
}

const newsKeyword = computed(() => latestData.value?.name || symbol.value)

onMounted(loadData)
watch([market, symbol, period], loadData)
</script>

<template>
  <div>
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-4">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">{{ symbol }}</h1>
        <p v-if="latestData?.name" class="text-gray-500">{{ latestData.name }}</p>
      </div>
      <div v-if="latestData" class="mt-2 sm:mt-0 flex items-center gap-4">
        <span class="text-2xl font-bold font-mono">{{ latestData.close.toFixed(2) }}</span>
        <span
          class="text-lg font-mono"
          :class="latestData.change_pct != null && latestData.change_pct >= 0 ? 'text-red-600' : 'text-green-600'"
        >
          {{ latestData.change_pct != null ? (latestData.change_pct >= 0 ? '+' : '') + latestData.change_pct.toFixed(2) + '%' : '' }}
        </span>
      </div>
    </div>

    <!-- Period selector -->
    <div class="flex gap-2 mb-4">
      <button
        v-for="p in ['daily', 'weekly', 'monthly']"
        :key="p"
        @click="period = p"
        :class="[
          'px-3 py-1 text-sm rounded-md transition',
          period === p ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200',
        ]"
      >
        {{ p.charAt(0).toUpperCase() + p.slice(1) }}
      </button>
    </div>

    <!-- K-line chart -->
    <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-6">
      <div v-if="loading" class="h-96 flex items-center justify-center text-gray-500">Loading chart...</div>
      <div v-else-if="klineData.length === 0" class="h-96 flex items-center justify-center text-gray-500">
        No K-line data available
      </div>
      <KlineChart v-else :data="klineData" :symbol="symbol" />
    </div>

    <!-- Data summary -->
    <div v-if="latestData" class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
      <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <p class="text-xs text-gray-500">Open</p>
        <p class="text-lg font-mono font-medium">{{ latestData.open.toFixed(2) }}</p>
      </div>
      <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <p class="text-xs text-gray-500">High</p>
        <p class="text-lg font-mono font-medium">{{ latestData.high.toFixed(2) }}</p>
      </div>
      <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <p class="text-xs text-gray-500">Low</p>
        <p class="text-lg font-mono font-medium">{{ latestData.low.toFixed(2) }}</p>
      </div>
      <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <p class="text-xs text-gray-500">Volume</p>
        <p class="text-lg font-mono font-medium">{{ latestData.volume.toLocaleString() }}</p>
      </div>
    </div>

    <!-- Related News -->
    <div class="mb-6">
      <RelatedNews :keyword="newsKeyword" />
    </div>

    <!-- AI Analysis section -->
    <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-lg font-bold text-gray-900">AI Analysis</h2>
        <button
          @click="generateReport"
          :disabled="aiLoading"
          class="bg-blue-600 text-white px-4 py-1.5 rounded-md text-sm hover:bg-blue-700 transition disabled:opacity-50"
        >
          {{ aiLoading ? 'Generating...' : 'Generate Report' }}
        </button>
      </div>
      <div v-if="aiLoading" class="text-center py-8">
        <div class="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
        <p class="text-gray-500 mt-2 text-sm">Analyzing with AI...</p>
      </div>
      <div v-else-if="aiReport" class="prose max-w-none text-sm text-gray-700 leading-relaxed whitespace-pre-line">
        {{ aiReport.content_md }}
      </div>
      <div v-else class="text-center py-8 text-gray-400 text-sm">
        Click "Generate Report" to get AI-powered analysis
      </div>
    </div>
  </div>
</template>
