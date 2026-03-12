<script setup lang="ts">
import { ref, onMounted } from 'vue'
import {
  getOverview,
  getAllocation,
  getHoldings,
  getCashFlows,
  getPerformance,
  type AssetOverview,
  type MarketAllocation,
  type HoldingItem,
  type CashFlowItem,
  type PerformancePoint,
} from '../api/portfolio'
import AssetPieChart from '../components/AssetPieChart.vue'
import PerformanceCurve from '../components/PerformanceCurve.vue'
import HoldingsTable from '../components/HoldingsTable.vue'

const overview = ref<AssetOverview | null>(null)
const allocation = ref<MarketAllocation[]>([])
const holdings = ref<HoldingItem[]>([])
const cashFlows = ref<CashFlowItem[]>([])
const performance = ref<PerformancePoint[]>([])
const loading = ref(false)

function pnlColor(val: number): string {
  if (val > 0) return 'text-red-600'
  if (val < 0) return 'text-green-600'
  return 'text-gray-500'
}

async function load() {
  loading.value = true
  try {
    const [o, a, h, c, p] = await Promise.all([
      getOverview(),
      getAllocation(),
      getHoldings(),
      getCashFlows(30),
      getPerformance(90),
    ])
    overview.value = o
    allocation.value = a
    holdings.value = h
    cashFlows.value = c
    performance.value = p
  } catch {
    // Silently handle — user may not be logged in
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <div>
    <h1 class="text-2xl font-bold text-gray-900 mb-4">Portfolio</h1>

    <div v-if="loading" class="text-center py-12 text-gray-500">Loading...</div>

    <div v-else-if="!overview || overview.account_count === 0" class="text-center py-12">
      <p class="text-gray-500 mb-4">No trading accounts yet.</p>
      <router-link
        to="/accounts"
        class="bg-blue-600 text-white px-4 py-2 rounded-md text-sm hover:bg-blue-700 transition"
      >
        Create Account
      </router-link>
    </div>

    <template v-else>
      <!-- Summary Cards -->
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div class="bg-white rounded-lg shadow p-4">
          <div class="text-xs text-gray-500 mb-1">Total Assets</div>
          <div class="text-xl font-bold">¥{{ Number(overview.total_value).toLocaleString() }}</div>
        </div>
        <div class="bg-white rounded-lg shadow p-4">
          <div class="text-xs text-gray-500 mb-1">Cash Balance</div>
          <div class="text-xl font-bold">¥{{ Number(overview.total_balance).toLocaleString() }}</div>
        </div>
        <div class="bg-white rounded-lg shadow p-4">
          <div class="text-xs text-gray-500 mb-1">Market Value</div>
          <div class="text-xl font-bold">¥{{ Number(overview.total_market_value).toLocaleString() }}</div>
        </div>
        <div class="bg-white rounded-lg shadow p-4">
          <div class="text-xs text-gray-500 mb-1">Total P&L</div>
          <div class="text-xl font-bold" :class="pnlColor(Number(overview.total_pnl))">
            {{ Number(overview.total_pnl) >= 0 ? '+' : '' }}¥{{ Number(overview.total_pnl).toLocaleString() }}
            <span class="text-sm font-normal ml-1">
              ({{ Number(overview.total_pnl_pct) >= 0 ? '+' : '' }}{{ Number(overview.total_pnl_pct).toFixed(2) }}%)
            </span>
          </div>
        </div>
      </div>

      <!-- P&L breakdown -->
      <div class="grid grid-cols-2 md:grid-cols-3 gap-4 mb-6">
        <div class="bg-white rounded-lg shadow p-4">
          <div class="text-xs text-gray-500 mb-1">Unrealized P&L</div>
          <div class="text-lg font-semibold" :class="pnlColor(Number(overview.total_unrealized_pnl))">
            {{ Number(overview.total_unrealized_pnl) >= 0 ? '+' : '' }}¥{{ Number(overview.total_unrealized_pnl).toLocaleString() }}
          </div>
        </div>
        <div class="bg-white rounded-lg shadow p-4">
          <div class="text-xs text-gray-500 mb-1">Realized P&L</div>
          <div class="text-lg font-semibold" :class="pnlColor(Number(overview.total_realized_pnl))">
            {{ Number(overview.total_realized_pnl) >= 0 ? '+' : '' }}¥{{ Number(overview.total_realized_pnl).toLocaleString() }}
          </div>
        </div>
        <div class="bg-white rounded-lg shadow p-4">
          <div class="text-xs text-gray-500 mb-1">Accounts</div>
          <div class="text-lg font-semibold">{{ overview.account_count }}</div>
        </div>
      </div>

      <!-- Performance Curve -->
      <div v-if="performance.length > 0" class="bg-white rounded-lg shadow p-4 mb-6">
        <h3 class="text-sm font-semibold text-gray-700 mb-2">Portfolio Performance</h3>
        <PerformanceCurve :data="performance" />
      </div>

      <!-- Charts + Holdings -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-6">
        <div class="bg-white rounded-lg shadow p-4">
          <h3 class="text-sm font-semibold text-gray-700 mb-2">Asset Allocation</h3>
          <AssetPieChart :data="allocation" />
        </div>
        <div class="lg:col-span-2">
          <HoldingsTable :holdings="holdings" />
        </div>
      </div>

      <!-- Cash Flows -->
      <div class="bg-white rounded-lg shadow overflow-hidden">
        <div class="px-4 py-3 border-b border-gray-200">
          <h3 class="text-sm font-semibold text-gray-700">Recent Cash Flows</h3>
        </div>
        <div v-if="cashFlows.length === 0" class="px-4 py-8 text-center text-gray-400 text-sm">
          No transactions yet
        </div>
        <div v-else class="overflow-x-auto">
          <table class="min-w-full text-sm">
            <thead class="bg-gray-50">
              <tr>
                <th class="px-3 py-2 text-left text-xs font-medium text-gray-500">Time</th>
                <th class="px-3 py-2 text-left text-xs font-medium text-gray-500">Account</th>
                <th class="px-3 py-2 text-left text-xs font-medium text-gray-500">Symbol</th>
                <th class="px-3 py-2 text-left text-xs font-medium text-gray-500">Side</th>
                <th class="px-3 py-2 text-right text-xs font-medium text-gray-500">Qty</th>
                <th class="px-3 py-2 text-right text-xs font-medium text-gray-500">Price</th>
                <th class="px-3 py-2 text-right text-xs font-medium text-gray-500">Amount</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-100">
              <tr v-for="cf in cashFlows" :key="cf.id" class="hover:bg-gray-50">
                <td class="px-3 py-2 text-gray-500">
                  {{ new Date(cf.filled_at).toLocaleString() }}
                </td>
                <td class="px-3 py-2 text-gray-500">{{ cf.account_name }}</td>
                <td class="px-3 py-2 font-medium">{{ cf.symbol }}</td>
                <td class="px-3 py-2">
                  <span
                    :class="cf.side === 'buy' ? 'text-red-600' : 'text-green-600'"
                    class="font-medium"
                  >
                    {{ cf.side === 'buy' ? 'Buy' : 'Sell' }}
                  </span>
                </td>
                <td class="px-3 py-2 text-right">{{ cf.quantity.toLocaleString() }}</td>
                <td class="px-3 py-2 text-right">{{ Number(cf.price).toFixed(2) }}</td>
                <td class="px-3 py-2 text-right" :class="pnlColor(Number(cf.amount))">
                  {{ Number(cf.amount) >= 0 ? '+' : '' }}¥{{ Number(cf.amount).toLocaleString() }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>
  </div>
</template>
