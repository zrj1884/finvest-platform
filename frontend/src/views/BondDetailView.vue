<script setup lang="ts">
import { ref, computed, onMounted, watch, shallowRef } from 'vue'
import { useRoute } from 'vue-router'
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

const route = useRoute()
const symbol = computed(() => route.params.symbol as string)

const bondHistory = ref<BondDaily[]>([])
const latestData = ref<BondDaily | null>(null)
const loading = ref(false)

const chartRef = ref<HTMLDivElement>()
const chart = shallowRef<echarts.ECharts>()

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

function renderChart() {
  if (!chartRef.value || !bondHistory.value.length) return

  if (!chart.value) {
    chart.value = echarts.init(chartRef.value)
  }

  const dates = bondHistory.value.map((d) => d.time.split('T')[0])
  const prices = bondHistory.value.map((d) => d.close)
  const volumes = bondHistory.value.map((d) => d.volume)

  chart.value.setOption({
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
      { type: 'inside', xAxisIndex: [0, 1], start: 60, end: 100 },
      { type: 'slider', xAxisIndex: [0, 1], start: 60, end: 100, top: '92%' },
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
  })
}

const newsKeyword = computed(() => latestData.value?.name || symbol.value)

onMounted(async () => {
  await loadData()
  renderChart()
})
watch(symbol, async () => {
  await loadData()
  renderChart()
})

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
    <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-6">
      <div v-if="loading" class="h-96 flex items-center justify-center text-gray-500">Loading chart...</div>
      <div v-else-if="bondHistory.length === 0" class="h-96 flex items-center justify-center text-gray-500">
        No bond data available
      </div>
      <div v-else ref="chartRef" class="w-full h-96 md:h-[500px]"></div>
    </div>

    <!-- Data summary -->
    <div v-if="latestData" class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
      <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <p class="text-xs text-gray-500">Close</p>
        <p class="text-lg font-mono font-medium">{{ latestData.close.toFixed(3) }}</p>
      </div>
      <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <p class="text-xs text-gray-500">Type</p>
        <p class="text-lg font-mono font-medium">{{ latestData.bond_type || '-' }}</p>
      </div>
      <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <p class="text-xs text-gray-500">Volume</p>
        <p class="text-lg font-mono font-medium">{{ latestData.volume.toLocaleString() }}</p>
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
