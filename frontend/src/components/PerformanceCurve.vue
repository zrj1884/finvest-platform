<script setup lang="ts">
import { ref, onMounted, watch, shallowRef } from 'vue'
import { useI18n } from 'vue-i18n'
import * as echarts from 'echarts/core'
import { LineChart } from 'echarts/charts'
import {
  GridComponent,
  TooltipComponent,
  DataZoomComponent,
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import type { PerformancePoint } from '../api/portfolio'

echarts.use([LineChart, GridComponent, TooltipComponent, DataZoomComponent, CanvasRenderer])

const { t } = useI18n()

const props = defineProps<{
  data: PerformancePoint[]
}>()

const chartRef = ref<HTMLDivElement>()
const chart = shallowRef<echarts.ECharts>()

function render() {
  if (!chart.value || !props.data.length) return

  const dates = props.data.map((d) => d.date)
  const values = props.data.map((d) => Number(d.total_value))

  const minVal = Math.min(...values)
  const maxVal = Math.max(...values)
  const padding = (maxVal - minVal) * 0.1 || maxVal * 0.05

  chart.value.setOption({
    tooltip: {
      trigger: 'axis',
      formatter: (params: Array<{ axisValue: string; value: number }>) => {
        const p = params[0]
        if (!p) return ''
        return `${p.axisValue}<br/>${t('chart.total')}: ¥${Number(p.value).toLocaleString()}`
      },
    },
    grid: { left: 80, right: 20, top: 20, bottom: 50 },
    xAxis: {
      type: 'category',
      data: dates,
      axisLabel: { fontSize: 11 },
    },
    yAxis: {
      type: 'value',
      min: Math.floor(minVal - padding),
      max: Math.ceil(maxVal + padding),
      axisLabel: {
        formatter: (v: number) => `¥${(v / 10000).toFixed(0)}`,
        fontSize: 11,
      },
    },
    dataZoom: [
      { type: 'inside', start: 0, end: 100 },
    ],
    series: [
      {
        type: 'line',
        data: values,
        smooth: true,
        symbol: 'circle',
        symbolSize: 4,
        lineStyle: { width: 2, color: '#3b82f6' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(59,130,246,0.3)' },
            { offset: 1, color: 'rgba(59,130,246,0.02)' },
          ]),
        },
        itemStyle: { color: '#3b82f6' },
      },
    ],
  })
}

onMounted(() => {
  if (chartRef.value) {
    chart.value = echarts.init(chartRef.value)
    render()
    window.addEventListener('resize', () => chart.value?.resize())
  }
})

watch(() => props.data, render, { deep: true })
</script>

<template>
  <div ref="chartRef" class="w-full h-64"></div>
</template>
