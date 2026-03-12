<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, shallowRef, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import * as echarts from 'echarts/core'
import { LineChart, BarChart } from 'echarts/charts'
import {
  GridComponent,
  TooltipComponent,
  DataZoomComponent,
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import RelatedNews from '../components/RelatedNews.vue'
import { getBondDaily, type BondDaily } from '../api/market'

echarts.use([LineChart, BarChart, GridComponent, TooltipComponent, DataZoomComponent, CanvasRenderer])

const { t } = useI18n()
const route = useRoute()
const symbol = computed(() => route.params.symbol as string)

const bondHistory = ref<BondDaily[]>([])
const latestData = ref<BondDaily | null>(null)
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
    const data = await getBondDaily(symbol.value, 500)
    bondHistory.value = [...data].reverse()
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
  const dates = bondHistory.value.map((d) => d.time.split('T')[0])
  const prices = bondHistory.value.map((d) => d.close)
  const volumes = bondHistory.value.map((d) => d.volume)
  const zoomStart = calcZoomStart(dates.length)

  return {
    tooltip: { trigger: 'axis' },
    grid: [
      { left: '8%', right: '3%', top: '5%', height: '55%' },
      { left: '8%', right: '3%', top: '68%', height: '18%' },
    ],
    xAxis: [
      { type: 'category', data: dates, gridIndex: 0, boundaryGap: false },
      { type: 'category', data: dates, gridIndex: 1, boundaryGap: true },
    ],
    yAxis: [
      { type: 'value', scale: true, gridIndex: 0, splitLine: { lineStyle: { color: '#f0f0f0' } } },
      { type: 'value', scale: true, gridIndex: 1, splitLine: { show: false } },
    ],
    dataZoom: [
      { type: 'inside', xAxisIndex: [0, 1], start: zoomStart, end: 100 },
      { type: 'slider', xAxisIndex: [0, 1], start: zoomStart, end: 100, top: '92%' },
    ],
    series: [
      {
        name: 'Price',
        type: 'line',
        data: prices,
        xAxisIndex: 0,
        yAxisIndex: 0,
        smooth: true,
        lineStyle: { width: 2, color: '#8b5cf6' },
        areaStyle: { color: 'rgba(139,92,246,0.08)' },
        symbol: 'none',
      },
      {
        name: 'Volume',
        type: 'bar',
        data: volumes,
        xAxisIndex: 1,
        yAxisIndex: 1,
        itemStyle: { color: '#94a3b8' },
      },
    ],
  }
}

function renderChart() {
  if (!chartRef.value || !bondHistory.value.length) return
  if (!chart.value) {
    chart.value = echarts.init(chartRef.value)
  }
  chart.value.setOption(buildOption())
}

function renderFsChart() {
  if (!fsChartRef.value || !bondHistory.value.length) return
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
        <span class="text-2xl font-bold font-mono">{{ latestData.close.toFixed(3) }}</span>
        <span
          v-if="latestData.change_pct != null"
          class="text-lg font-mono"
          :class="latestData.change_pct >= 0 ? 'text-red-600' : 'text-green-600'"
        >
          {{ (latestData.change_pct >= 0 ? '+' : '') + latestData.change_pct.toFixed(3) + '%' }}
        </span>
      </div>
    </div>

    <!-- Price Chart -->
    <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-6 relative">
      <div v-if="loading" class="h-96 flex items-center justify-center text-gray-500">{{ t('chart.loading') }}</div>
      <div v-else-if="bondHistory.length === 0" class="h-96 flex items-center justify-center text-gray-500">
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
          <span class="font-bold text-gray-800">{{ symbol }} — {{ latestData?.name || t('market.bond') }}</span>
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
        <p class="text-xs text-gray-500">{{ t('table.close') }}</p>
        <p class="text-lg font-mono font-medium">{{ latestData.close.toFixed(3) }}</p>
      </div>
      <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <p class="text-xs text-gray-500">{{ t('table.bondType') }}</p>
        <p class="text-lg font-mono font-medium">{{ latestData.bond_type || '-' }}</p>
      </div>
      <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <p class="text-xs text-gray-500">{{ t('table.volume') }}</p>
        <p class="text-lg font-mono font-medium">{{ latestData.volume.toLocaleString() }}</p>
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
