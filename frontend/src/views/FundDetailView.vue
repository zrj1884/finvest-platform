<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, shallowRef, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
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

const { t } = useI18n()
const route = useRoute()
const symbol = computed(() => route.params.symbol as string)

const navHistory = ref<FundNav[]>([])
const latestData = ref<FundNav | null>(null)
const loading = ref(false)

const chartRef = ref<HTMLDivElement>()
const chart = shallowRef<echarts.ECharts>()

const fullscreen = ref(false)
const fsChartRef = ref<HTMLDivElement>()
const fsChart = shallowRef<echarts.ECharts>()

const DEFAULT_VISIBLE_BARS = 50

async function loadData() {
  loading.value = true
  try {
    const data = await getFundNav(symbol.value, 500)
    navHistory.value = [...data].reverse()
    latestData.value = data[0] ?? null
  } catch {
    // ignore
  } finally {
    loading.value = false
  }
}

function calcZoomStart(total: number): number {
  if (total <= DEFAULT_VISIBLE_BARS) return 0
  return Math.round(((total - DEFAULT_VISIBLE_BARS) / total) * 100)
}

function buildOption() {
  const dates = navHistory.value.map((d) => d.time.split('T')[0])
  const navs = navHistory.value.map((d) => d.nav)
  const zoomStart = calcZoomStart(dates.length)

  return {
    tooltip: { trigger: 'axis' },
    grid: { left: '8%', right: '3%', top: '5%', bottom: '15%' },
    xAxis: { type: 'category', data: dates, boundaryGap: false },
    yAxis: { type: 'value', scale: true, splitLine: { lineStyle: { color: '#f0f0f0' } } },
    dataZoom: [
      { type: 'inside', start: zoomStart, end: 100 },
      { type: 'slider', start: zoomStart, end: 100 },
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
  }
}

function renderChart() {
  if (!chartRef.value || !navHistory.value.length) return
  if (!chart.value) {
    chart.value = echarts.init(chartRef.value)
  }
  chart.value.setOption(buildOption())
}

function renderFsChart() {
  if (!fsChartRef.value || !navHistory.value.length) return
  if (!fsChart.value) {
    fsChart.value = echarts.init(fsChartRef.value)
  }
  fsChart.value.setOption(buildOption())
}

function openFullscreen() {
  fullscreen.value = true
  nextTick(() => {
    renderFsChart()
  })
}

function closeFullscreen() {
  fullscreen.value = false
  if (fsChart.value) {
    fsChart.value.dispose()
    fsChart.value = undefined
  }
}

function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape' && fullscreen.value) {
    closeFullscreen()
  }
}

function onResize() {
  chart.value?.resize()
  fsChart.value?.resize()
}

onMounted(async () => {
  await loadData()
  renderChart()
  window.addEventListener('keydown', onKeydown)
  window.addEventListener('resize', onResize)
})

onUnmounted(() => {
  window.removeEventListener('keydown', onKeydown)
  window.removeEventListener('resize', onResize)
  chart.value?.dispose()
  fsChart.value?.dispose()
})

watch(symbol, async () => {
  await loadData()
  renderChart()
})

const newsKeyword = computed(() => latestData.value?.name || symbol.value)
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
    <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-6 relative">
      <div v-if="loading" class="h-96 flex items-center justify-center text-gray-500">{{ t('chart.loading') }}</div>
      <div v-else-if="navHistory.length === 0" class="h-96 flex items-center justify-center text-gray-500">
        {{ t('chart.noData') }}
      </div>
      <template v-else>
        <div ref="chartRef" class="w-full h-96 md:h-[500px]"></div>
        <!-- Fullscreen button -->
        <button
          @click="openFullscreen"
          class="absolute top-6 right-6 p-1.5 rounded-md bg-white/80 hover:bg-white border border-gray-200 text-gray-500 hover:text-gray-700 transition"
          :title="t('chart.fullscreen')"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5v-4m0 4h-4m4 0l-5-5" />
          </svg>
        </button>
      </template>
    </div>

    <!-- Fullscreen overlay -->
    <Teleport to="body">
      <div
        v-if="fullscreen"
        class="fixed inset-0 z-[9999] bg-white flex flex-col"
      >
        <div class="flex items-center justify-between px-4 py-2 border-b border-gray-200">
          <span class="font-bold text-gray-800">{{ symbol }} — {{ t('table.nav') }}</span>
          <button
            @click="closeFullscreen"
            class="px-3 py-1 text-sm rounded-md bg-gray-100 hover:bg-gray-200 text-gray-600 transition"
          >
            {{ t('chart.exitFullscreen') }} (ESC)
          </button>
        </div>
        <div ref="fsChartRef" class="flex-1"></div>
      </div>
    </Teleport>

    <!-- Data summary -->
    <div v-if="latestData" class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
      <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <p class="text-xs text-gray-500">{{ t('table.nav') }}</p>
        <p class="text-lg font-mono font-medium">{{ latestData.nav.toFixed(4) }}</p>
      </div>
      <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <p class="text-xs text-gray-500">{{ t('table.accNav') }}</p>
        <p class="text-lg font-mono font-medium">{{ latestData.accumulated_nav?.toFixed(4) || '-' }}</p>
      </div>
      <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <p class="text-xs text-gray-500">{{ t('table.dailyReturn') }}</p>
        <p class="text-lg font-mono font-medium">{{ latestData.daily_return != null ? latestData.daily_return.toFixed(2) + '%' : '-' }}</p>
      </div>
      <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <p class="text-xs text-gray-500">{{ t('table.date') }}</p>
        <p class="text-lg font-mono font-medium">{{ latestData.time.split('T')[0] }}</p>
      </div>
    </div>

    <!-- Related News -->
    <RelatedNews :keyword="newsKeyword" />
  </div>
</template>
