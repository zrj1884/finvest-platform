<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { listOrders, cancelOrder, type OrderRecord } from '../api/trading'

const props = defineProps<{
  accountId: string
}>()

const orders = ref<OrderRecord[]>([])
const loading = ref(false)

async function loadOrders() {
  if (!props.accountId) return
  loading.value = true
  try {
    orders.value = await listOrders(props.accountId, undefined, undefined, 50)
  } catch {
    orders.value = []
  } finally {
    loading.value = false
  }
}

async function handleCancel(orderId: string) {
  try {
    await cancelOrder(orderId)
    await loadOrders()
  } catch {
    // ignore
  }
}

function statusColor(status: string): string {
  switch (status) {
    case 'filled':
      return 'bg-green-100 text-green-700'
    case 'cancelled':
    case 'rejected':
      return 'bg-gray-100 text-gray-500'
    case 'pending':
    case 'submitted':
      return 'bg-yellow-100 text-yellow-700'
    case 'partial_filled':
      return 'bg-blue-100 text-blue-700'
    default:
      return 'bg-gray-100 text-gray-600'
  }
}

function formatTime(iso: string | null): string {
  if (!iso) return '-'
  return new Date(iso).toLocaleString('zh-CN', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
}

onMounted(loadOrders)
watch(() => props.accountId, loadOrders)

defineExpose({ refresh: loadOrders })
</script>

<template>
  <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
    <h3 class="text-sm font-bold text-gray-900 mb-3">Orders</h3>

    <div v-if="loading" class="text-center py-4 text-gray-500 text-sm">Loading...</div>
    <div v-else-if="orders.length === 0" class="text-center py-4 text-gray-400 text-sm">No orders</div>

    <div v-else class="overflow-x-auto">
      <table class="w-full text-xs">
        <thead>
          <tr class="text-left text-gray-500 border-b">
            <th class="pb-2 pr-2">Symbol</th>
            <th class="pb-2 pr-2">Side</th>
            <th class="pb-2 pr-2">Type</th>
            <th class="pb-2 pr-2 text-right">Qty</th>
            <th class="pb-2 pr-2 text-right">Price</th>
            <th class="pb-2 pr-2 text-right">Filled</th>
            <th class="pb-2 pr-2">Status</th>
            <th class="pb-2 pr-2">Time</th>
            <th class="pb-2"></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="o in orders" :key="o.id" class="border-b border-gray-50 hover:bg-gray-50">
            <td class="py-1.5 pr-2 font-mono">{{ o.symbol }}</td>
            <td class="py-1.5 pr-2">
              <span :class="o.side === 'buy' ? 'text-red-600' : 'text-green-600'" class="font-medium">
                {{ o.side.toUpperCase() }}
              </span>
            </td>
            <td class="py-1.5 pr-2">{{ o.order_type }}</td>
            <td class="py-1.5 pr-2 text-right font-mono">{{ o.quantity }}</td>
            <td class="py-1.5 pr-2 text-right font-mono">{{ o.filled_price?.toFixed(2) || o.price?.toFixed(2) || '-' }}</td>
            <td class="py-1.5 pr-2 text-right font-mono">{{ o.filled_quantity }}</td>
            <td class="py-1.5 pr-2">
              <span :class="statusColor(o.status)" class="px-1.5 py-0.5 rounded text-xs font-medium">
                {{ o.status }}
              </span>
            </td>
            <td class="py-1.5 pr-2 text-gray-400">{{ formatTime(o.created_at) }}</td>
            <td class="py-1.5">
              <button
                v-if="o.status === 'pending' || o.status === 'submitted' || o.status === 'partial_filled'"
                @click="handleCancel(o.id)"
                class="text-red-500 hover:text-red-700 text-xs"
              >
                Cancel
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
