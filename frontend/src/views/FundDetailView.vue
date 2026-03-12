<script setup lang="ts">
import { ref, computed, onMounted, watch, shallowRef } from 'vue'
import { useRoute } from 'vue-router'
import * as echarts from 'echarts/core'
import { LineChart } from 'echarts/charts'
import {
  GridComponent,
  TooltipComponent,
  DataZoomComponent,
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import RelatedNews from '../components/RelatedNews.vue'
import { getFundNav, type FundNav } from '../api/market'

echarts.use([LineChart, GridComponent, TooltipComponent, DataZoomComponent, CanvasRenderer])

const route = useRoute()
const symbol = computed(() => route.params.symbol as string)

const navHistory = ref<FundNav[]>([])
const latestData = ref<FundNav | null>(null)
const loading = ref(false)

const chartRef = ref<HTMLDivElement>()
const chart = shallowRef<echarts.ECharts>()

async function loadData() {
  loading.value = true
  try {
    const data = await getFundNav(symbol.value, 500)
    // API returns DESC order, reverse for charting
    navHistory.value = [...data].reverse()
    latestData.value = data[0] ?? null
  } catch {
    // ignore
  } finally {
    loading.value = false
  }
}

function renderChart() {
  if (!chartRef.value || !navHistory.value.length) return

  if (!chart.value) {
    chart.value = echarts.init(chartRef.value)
  }

  const dates = navHistory.value.map((d) => d.time.split('T')[0])
  const navs = navHistory.value.map((d) => d.nav)

  chart.value.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: '8%', right: '3%', top: '5%', bottom: '15%' },
    xAxis: { type: 'category', data: dates, boundaryGap: false },
    yAxis: { type: 'value', scale: true, splitLine: { lineStyle: { color: '#f0f0f0' } } },
    dataZoom: [
      { type: 'inside', start: 60, end: 100 },
      { type: 'slider', start: 60, end: 100 },
    ],
    series: [
      {
        name: 'NAV',
        type: 'line',
        data: navs,
        smooth: true,
        lineStyle: { width: 2, color: '#3b82f6' },
        areaStyle: { color: 'rgba(59,130,246,0.08)' },
        symbol: 'none',
      },
    ],
  })
}

onMounted(async () => {
  await loadData()
  renderChart()
})
watch(symbol, async () => {
  await loadData()
  renderChart()
})

const newsKeyword = computed(() => latestData.value?.name || symbol.value)

if (typeof window !== 'undefined') {
  window.addEventListener('resize', () => chart.value?.resize())
}
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
        <span class="text-2xl font-bold font-mono">{{ latestData.nav.toFixed(4) }}</span>
        <span
          v-if="latestData.daily_return != null"
          class="text-lg font-mono"
          :class="latestData.daily_return >= 0 ? 'text-red-600' : 'text-green-600'"
        >
          {{ (latestData.daily_return >= 0 ? '+' : '') + latestData.daily_return.toFixed(2) + '%' }}
        </span>
      </div>
    </div>

    <!-- NAV Chart -->
    <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-6">
      <div v-if="loading" class="h-96 flex items-center justify-center text-gray-500">Loading chart...</div>
      <div v-else-if="navHistory.length === 0" class="h-96 flex items-center justify-center text-gray-500">
        No NAV data available
      </div>
      <div v-else ref="chartRef" class="w-full h-96 md:h-[500px]"></div>
    </div>

    <!-- Data summary -->
    <div v-if="latestData" class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
      <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <p class="text-xs text-gray-500">NAV</p>
        <p class="text-lg font-mono font-medium">{{ latestData.nav.toFixed(4) }}</p>
      </div>
      <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <p class="text-xs text-gray-500">Accumulated NAV</p>
        <p class="text-lg font-mono font-medium">{{ latestData.accumulated_nav?.toFixed(4) || '-' }}</p>
      </div>
      <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <p class="text-xs text-gray-500">Daily Return</p>
        <p class="text-lg font-mono font-medium">{{ latestData.daily_return != null ? latestData.daily_return.toFixed(2) + '%' : '-' }}</p>
      </div>
      <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <p class="text-xs text-gray-500">Date</p>
        <p class="text-lg font-mono font-medium">{{ latestData.time.split('T')[0] }}</p>
      </div>
    </div>

    <!-- Related News -->
    <RelatedNews :keyword="newsKeyword" />
  </div>
</template>
