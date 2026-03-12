<script setup lang="ts">
import { ref, onMounted, watch, shallowRef } from 'vue'
import { useI18n } from 'vue-i18n'
import * as echarts from 'echarts/core'
import { PieChart } from 'echarts/charts'
import { TooltipComponent, LegendComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import type { MarketAllocation } from '../api/portfolio'

echarts.use([PieChart, TooltipComponent, LegendComponent, CanvasRenderer])

const { t } = useI18n()

const props = defineProps<{
  data: MarketAllocation[]
}>()

const chartRef = ref<HTMLDivElement>()
const chart = shallowRef<echarts.ECharts>()

function marketLabel(market: string): string {
  return t(`market.${market}`)
}

function render() {
  if (!chart.value || !props.data.length) return
  chart.value.setOption({
    tooltip: {
      trigger: 'item',
      formatter: '{b}: ¥{c} ({d}%)',
    },
    legend: {
      bottom: 0,
      data: props.data.map((d) => marketLabel(d.market)),
    },
    series: [
      {
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: true,
        itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
        label: { show: true, formatter: '{b}\n{d}%' },
        data: props.data.map((d) => ({
          name: marketLabel(d.market),
          value: Number(d.total_value),
        })),
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
