<script setup lang="ts">
import { ref, onMounted, watch, shallowRef } from 'vue'
import * as echarts from 'echarts/core'
import { CandlestickChart, BarChart } from 'echarts/charts'
import {
  GridComponent,
  TooltipComponent,
  DataZoomComponent,
  LegendComponent,
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
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

const props = defineProps<{
  data: KlineData[]
  symbol: string
}>()

const chartRef = ref<HTMLDivElement>()
const chart = shallowRef<echarts.ECharts>()

function renderChart() {
  if (!chartRef.value || !props.data.length) return

  if (!chart.value) {
    chart.value = echarts.init(chartRef.value)
  }

  const dates = props.data.map((d) => d[0].split('T')[0])
  const ohlc = props.data.map((d) => [d[1], d[2], d[3], d[4]]) // open, close, low, high
  const volumes = props.data.map((d) => d[5])

  chart.value.setOption({
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
      { type: 'inside', xAxisIndex: [0, 1], start: 60, end: 100 },
      { type: 'slider', xAxisIndex: [0, 1], start: 60, end: 100, top: '94%' },
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
  })
}

onMounted(renderChart)
watch(() => props.data, renderChart)

// Responsive resize
if (typeof window !== 'undefined') {
  window.addEventListener('resize', () => chart.value?.resize())
}
</script>

<template>
  <div ref="chartRef" class="w-full h-96 md:h-[500px]"></div>
</template>
