<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { listOrders, cancelOrder, type OrderRecord } from '../api/trading'

const { t, locale } = useI18n()

const props = defineProps<{
  accountId: string
}>()

const orders = ref<OrderRecord[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 20
const loading = ref(false)

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize)))

async function loadOrders() {
  if (!props.accountId) return
  loading.value = true
  try {
    const offset = (page.value - 1) * pageSize
    const resp = await listOrders(props.accountId, undefined, undefined, pageSize, offset)
    orders.value = resp.items
    total.value = resp.total
  } catch {
    orders.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

async function handleCancel(orderId: string) {
  if (!confirm(t('trading.cancelConfirm'))) return
  try {
    await cancelOrder(orderId)
    await loadOrders()
  } catch {
    // ignore
  }
}

function prevPage() {
  if (page.value > 1) {
    page.value--
    loadOrders()
  }
}

function nextPage() {
  if (page.value < totalPages.value) {
    page.value++
    loadOrders()
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

function statusLabel(status: string): string {
  return t(`order.${status}`)
}

function formatTime(iso: string | null): string {
  if (!iso) return '-'
  const loc = locale.value === 'zh' ? 'zh-CN' : 'en-US'
  return new Date(iso).toLocaleString(loc, {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
}

onMounted(loadOrders)
watch(
  () => props.accountId,
  () => {
    page.value = 1
    loadOrders()
  },
)

defineExpose({ refresh: loadOrders })
</script>

<template>
  <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
    <h3 class="text-sm font-bold text-gray-900 mb-3">{{ t('order.title') }}</h3>

    <div v-if="loading" class="text-center py-4 text-gray-500 text-sm">{{ t('common.loading') }}</div>
    <div v-else-if="orders.length === 0" class="text-center py-4 text-gray-400 text-sm">{{ t('order.noOrders') }}</div>

    <template v-else>
      <div class="overflow-x-auto">
        <table class="w-full text-xs">
          <thead>
            <tr class="text-left text-gray-500 border-b">
              <th class="pb-2 pr-2">{{ t('common.symbol') }}</th>
              <th class="pb-2 pr-2">{{ t('common.side') }}</th>
              <th class="pb-2 pr-2">{{ t('common.type') }}</th>
              <th class="pb-2 pr-2 text-right">{{ t('common.qty') }}</th>
              <th class="pb-2 pr-2 text-right">{{ t('common.price') }}</th>
              <th class="pb-2 pr-2 text-right">{{ t('order.filledPrice') }}</th>
              <th class="pb-2 pr-2">{{ t('common.status') }}</th>
              <th class="pb-2 pr-2">{{ t('common.time') }}</th>
              <th class="pb-2"></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="o in orders" :key="o.id" class="border-b border-gray-50 hover:bg-gray-50">
              <td class="py-1.5 pr-2 font-mono">{{ o.symbol }}</td>
              <td class="py-1.5 pr-2">
                <span :class="o.side === 'buy' ? 'text-red-600' : 'text-green-600'" class="font-medium">
                  {{ o.side === 'buy' ? t('common.buy') : t('common.sell') }}
                </span>
              </td>
              <td class="py-1.5 pr-2">{{ o.order_type === 'market' ? t('trading.marketOrder') : t('trading.limitOrder') }}</td>
              <td class="py-1.5 pr-2 text-right font-mono">{{ o.quantity }}</td>
              <td class="py-1.5 pr-2 text-right font-mono">{{ o.price?.toFixed(2) || '-' }}</td>
              <td class="py-1.5 pr-2 text-right font-mono">{{ o.filled_price?.toFixed(2) || '-' }}</td>
              <td class="py-1.5 pr-2">
                <span :class="statusColor(o.status)" class="px-1.5 py-0.5 rounded text-xs font-medium">
                  {{ statusLabel(o.status) }}
                </span>
              </td>
              <td class="py-1.5 pr-2 text-gray-400">{{ formatTime(o.created_at) }}</td>
              <td class="py-1.5">
                <button
                  v-if="o.status === 'pending' || o.status === 'submitted' || o.status === 'partial_filled'"
                  @click="handleCancel(o.id)"
                  class="text-red-500 hover:text-red-700 text-xs"
                >
                  {{ t('common.cancel') }}
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Pagination -->
      <div v-if="totalPages > 1" class="flex items-center justify-between mt-3 text-xs text-gray-500">
        <span>{{ t('table.total', { total }) }}</span>
        <div class="flex items-center gap-2">
          <button
            @click="prevPage"
            :disabled="page <= 1"
            class="px-2 py-1 rounded border border-gray-300 hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {{ t('table.prev') }}
          </button>
          <span>{{ t('table.page', { page, pages: totalPages }) }}</span>
          <button
            @click="nextPage"
            :disabled="page >= totalPages"
            class="px-2 py-1 rounded border border-gray-300 hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {{ t('table.next') }}
          </button>
        </div>
      </div>
    </template>
  </div>
</template>
