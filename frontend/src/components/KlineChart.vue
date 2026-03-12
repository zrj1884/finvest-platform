<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, shallowRef, nextTick } from 'vue'
import * as echarts from 'echarts/core'
import { CandlestickChart, BarChart } from 'echarts/charts'
import {
  GridComponent,
  TooltipComponent,
  DataZoomComponent,
  LegendComponent,
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import { useI18n } from 'vue-i18n'
import type { KlineData } from '../api/market'

echarts.use([
  CandlestickChart,
  BarChart,
  GridComponent,
  TooltipComponent,
  DataZoomComponent,
  LegendComponent,
  CanvasRenderer,
])

const { t } = useI18n()

const props = withDefaults(
  defineProps<{
    data: KlineData[]
    symbol: string
    defaultVisibleBars?: number
  }>(),
  { defaultVisibleBars: 50 },
)

const chartRef = ref<HTMLDivElement>()
const chart = shallowRef<echarts.ECharts>()

const fullscreen = ref(false)
const fsChartRef = ref<HTMLDivElement>()
const fsChart = shallowRef<echarts.ECharts>()

function calcZoomStart(total: number): number {
  if (total <= props.defaultVisibleBars) return 0
  return Math.round(((total - props.defaultVisibleBars) / total) * 100)
}

function buildOption() {
  const dates = props.data.map((d) => d[0].split('T')[0])
  const ohlc = props.data.map((d) => [d[1], d[2], d[3], d[4]])
  const volumes = props.data.map((d) => d[5])
  const zoomStart = calcZoomStart(dates.length)

  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' },
    },
    grid: [
      { left: '8%', right: '3%', top: '5%', height: '60%' },
      { left: '8%', right: '3%', top: '72%', height: '18%' },
    ],
    xAxis: [
      { type: 'category', data: dates, gridIndex: 0, boundaryGap: true },
      { type: 'category', data: dates, gridIndex: 1, boundaryGap: true },
    ],
    yAxis: [
      { scale: true, gridIndex: 0, splitLine: { show: true, lineStyle: { color: '#f0f0f0' } } },
      { scale: true, gridIndex: 1, splitLine: { show: false } },
    ],
    dataZoom: [
      { type: 'inside', xAxisIndex: [0, 1], start: zoomStart, end: 100 },
      { type: 'slider', xAxisIndex: [0, 1], start: zoomStart, end: 100, top: '94%' },
    ],
    series: [
      {
        name: props.symbol,
        type: 'candlestick',
        data: ohlc,
        xAxisIndex: 0,
        yAxisIndex: 0,
        itemStyle: {
          color: '#ef4444',
          color0: '#22c55e',
          borderColor: '#ef4444',
          borderColor0: '#22c55e',
        },
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
  if (!chartRef.value || !props.data.length) return
  if (!chart.value) {
    chart.value = echarts.init(chartRef.value)
  }
  chart.value.setOption(buildOption())
}

function renderFsChart() {
  if (!fsChartRef.value || !props.data.length) return
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

onMounted(() => {
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

watch(() => props.data, renderChart)
</script>

<template>
  <div class="relative">
    <div ref="chartRef" class="w-full h-96 md:h-[500px]"></div>
    <!-- Fullscreen button -->
    <button
      @click="openFullscreen"
      class="absolute top-2 right-2 p-1.5 rounded-md bg-white/80 hover:bg-white border border-gray-200 text-gray-500 hover:text-gray-700 transition"
      :title="t('chart.fullscreen')"
    >
      <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
        <path stroke-linecap="round" stroke-linejoin="round" d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5v-4m0 4h-4m4 0l-5-5" />
      </svg>
    </button>

    <!-- Fullscreen overlay -->
    <Teleport to="body">
      <div
        v-if="fullscreen"
        class="fixed inset-0 z-[9999] bg-white flex flex-col"
      >
        <div class="flex items-center justify-between px-4 py-2 border-b border-gray-200">
          <span class="font-bold text-gray-800">{{ symbol }}</span>
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
  </div>
</template>
