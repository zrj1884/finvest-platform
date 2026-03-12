<script setup lang="ts">
import type { HoldingItem } from '../api/portfolio'

const MARKET_LABELS: Record<string, string> = {
  a_share: 'A股',
  us_stock: '美股',
  hk_stock: '港股',
  fund: '基金',
  bond: '债券',
}

defineProps<{
  holdings: HoldingItem[]
}>()

function pnlColor(val: number): string {
  if (val > 0) return 'text-red-600'
  if (val < 0) return 'text-green-600'
  return 'text-gray-500'
}
</script>

<template>
  <div class="bg-white rounded-lg shadow overflow-hidden">
    <div class="px-4 py-3 border-b border-gray-200">
      <h3 class="text-sm font-semibold text-gray-700">Holdings</h3>
    </div>
    <div v-if="holdings.length === 0" class="px-4 py-8 text-center text-gray-400 text-sm">
      No holdings
    </div>
    <div v-else class="overflow-x-auto">
      <table class="min-w-full text-sm">
        <thead class="bg-gray-50">
          <tr>
            <th class="px-3 py-2 text-left text-xs font-medium text-gray-500">Symbol</th>
            <th class="px-3 py-2 text-left text-xs font-medium text-gray-500">Market</th>
            <th class="px-3 py-2 text-left text-xs font-medium text-gray-500">Account</th>
            <th class="px-3 py-2 text-right text-xs font-medium text-gray-500">Qty</th>
            <th class="px-3 py-2 text-right text-xs font-medium text-gray-500">Avg Cost</th>
            <th class="px-3 py-2 text-right text-xs font-medium text-gray-500">Price</th>
            <th class="px-3 py-2 text-right text-xs font-medium text-gray-500">Market Value</th>
            <th class="px-3 py-2 text-right text-xs font-medium text-gray-500">P&L</th>
            <th class="px-3 py-2 text-right text-xs font-medium text-gray-500">P&L %</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-100">
          <tr v-for="h in holdings" :key="`${h.account_id}-${h.symbol}`" class="hover:bg-gray-50">
            <td class="px-3 py-2 font-medium">
              {{ h.symbol }}
              <span v-if="h.name" class="text-xs text-gray-400 ml-1">{{ h.name }}</span>
            </td>
            <td class="px-3 py-2 text-gray-500">{{ MARKET_LABELS[h.market] || h.market }}</td>
            <td class="px-3 py-2 text-gray-500">{{ h.account_name }}</td>
            <td class="px-3 py-2 text-right">{{ h.quantity.toLocaleString() }}</td>
            <td class="px-3 py-2 text-right">{{ Number(h.avg_cost).toFixed(2) }}</td>
            <td class="px-3 py-2 text-right">{{ Number(h.current_price).toFixed(2) }}</td>
            <td class="px-3 py-2 text-right">¥{{ Number(h.market_value).toLocaleString() }}</td>
            <td class="px-3 py-2 text-right" :class="pnlColor(Number(h.unrealized_pnl))">
              {{ Number(h.unrealized_pnl) >= 0 ? '+' : '' }}{{ Number(h.unrealized_pnl).toLocaleString() }}
            </td>
            <td class="px-3 py-2 text-right" :class="pnlColor(Number(h.unrealized_pnl_pct))">
              {{ Number(h.unrealized_pnl_pct) >= 0 ? '+' : '' }}{{ Number(h.unrealized_pnl_pct).toFixed(2) }}%
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
