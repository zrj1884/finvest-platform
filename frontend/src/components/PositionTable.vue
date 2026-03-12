<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { listPositions, type Position } from '../api/trading'

const { t } = useI18n()

const props = defineProps<{
  accountId: string
}>()

const positions = ref<Position[]>([])
const loading = ref(false)

async function loadPositions() {
  if (!props.accountId) return
  loading.value = true
  try {
    positions.value = (await listPositions(props.accountId)).filter((p) => p.quantity > 0)
  } catch {
    positions.value = []
  } finally {
    loading.value = false
  }
}

function pnlColor(value: number): string {
  if (value > 0) return 'text-red-600'
  if (value < 0) return 'text-green-600'
  return 'text-gray-500'
}

onMounted(loadPositions)
watch(() => props.accountId, loadPositions)

defineExpose({ refresh: loadPositions })
</script>

<template>
  <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
    <h3 class="text-sm font-bold text-gray-900 mb-3">{{ t('position.title') }}</h3>

    <div v-if="loading" class="text-center py-4 text-gray-500 text-sm">{{ t('common.loading') }}</div>
    <div v-else-if="positions.length === 0" class="text-center py-4 text-gray-400 text-sm">{{ t('position.noPositions') }}</div>

    <div v-else class="overflow-x-auto">
      <table class="w-full text-xs">
        <thead>
          <tr class="text-left text-gray-500 border-b">
            <th class="pb-2 pr-2">{{ t('common.symbol') }}</th>
            <th class="pb-2 pr-2">{{ t('common.name') }}</th>
            <th class="pb-2 pr-2 text-right">{{ t('common.qty') }}</th>
            <th class="pb-2 pr-2 text-right">{{ t('position.avail') }}</th>
            <th class="pb-2 pr-2 text-right">{{ t('position.avgCost') }}</th>
            <th class="pb-2 pr-2 text-right">{{ t('common.price') }}</th>
            <th class="pb-2 pr-2 text-right">{{ t('position.marketValue') }}</th>
            <th class="pb-2 pr-2 text-right">{{ t('position.pnl') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="p in positions" :key="p.id" class="border-b border-gray-50 hover:bg-gray-50">
            <td class="py-1.5 pr-2 font-mono font-medium">{{ p.symbol }}</td>
            <td class="py-1.5 pr-2 text-gray-600">{{ p.name || '-' }}</td>
            <td class="py-1.5 pr-2 text-right font-mono">{{ p.quantity }}</td>
            <td class="py-1.5 pr-2 text-right font-mono">{{ p.available_quantity }}</td>
            <td class="py-1.5 pr-2 text-right font-mono">{{ p.avg_cost.toFixed(2) }}</td>
            <td class="py-1.5 pr-2 text-right font-mono">{{ p.current_price.toFixed(2) }}</td>
            <td class="py-1.5 pr-2 text-right font-mono">{{ p.market_value.toFixed(2) }}</td>
            <td class="py-1.5 pr-2 text-right font-mono" :class="pnlColor(p.unrealized_pnl)">
              {{ p.unrealized_pnl >= 0 ? '+' : '' }}{{ p.unrealized_pnl.toFixed(2) }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
