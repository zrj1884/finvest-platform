<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { getStockSnapshot, type StockDaily } from '../api/market'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()

const market = computed(() => (route.params.market as string) || 'a_share')
const stocks = ref<StockDaily[]>([])
const loading = ref(false)
const searchQuery = ref('')
const searchInput = ref('')

// Pagination
const page = ref(1)
const pageSize = ref(10)
const pageSizeOptions = [10, 20, 50]
const total = ref(0)
const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize.value)))

// Sorting
const sortBy = ref('symbol')
const sortOrder = ref<'asc' | 'desc'>('asc')

function toggleSort(field: string) {
  if (sortBy.value === field) {
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortBy.value = field
    sortOrder.value = field === 'change_pct' || field === 'volume' ? 'desc' : 'asc'
  }
  page.value = 1
  loadData()
}

function sortIcon(field: string): string {
  if (sortBy.value !== field) return '↕'
  return sortOrder.value === 'asc' ? '↑' : '↓'
}

async function loadData() {
  loading.value = true
  try {
    const resp = await getStockSnapshot(
      market.value, page.value, pageSize.value,
      sortBy.value, sortOrder.value,
      searchQuery.value || undefined,
    )
    stocks.value = resp.items
    total.value = resp.total
  } catch {
    stocks.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

function doSearch() {
  searchQuery.value = searchInput.value.trim()
  page.value = 1
  loadData()
}

function goToDetail(symbol: string) {
  router.push(`/stock/${market.value}/${symbol}`)
}

function changePage(p: number) {
  if (p < 1 || p > totalPages.value) return
  page.value = p
  loadData()
}

function changePageSize(size: number) {
  pageSize.value = size
  page.value = 1
  loadData()
}

onMounted(loadData)
watch(market, () => {
  page.value = 1
  searchQuery.value = ''
  searchInput.value = ''
  loadData()
})
</script>

<template>
  <div>
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6">
      <h1 class="text-2xl font-bold text-gray-900">{{ t(`market.${market}`) }}</h1>
      <div class="mt-3 sm:mt-0 flex gap-2">
        <input
          v-model="searchInput"
          @keyup.enter="doSearch"
          type="text"
          :placeholder="t('table.searchPlaceholder')"
          class="border border-gray-300 rounded-md px-3 py-1.5 text-sm focus:ring-blue-500 focus:border-blue-500"
        />
        <button
          @click="doSearch"
          class="bg-blue-600 text-white px-4 py-1.5 rounded-md text-sm hover:bg-blue-700 transition"
        >
          {{ t('table.search') }}
        </button>
      </div>
    </div>

    <div v-if="loading" class="text-center py-12 text-gray-500">{{ t('common.loading') }}</div>

    <div v-else-if="stocks.length === 0" class="text-center py-12 text-gray-500">
      {{ t('table.noData') }}
    </div>

    <template v-else>
      <div class="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        <div class="overflow-x-auto">
          <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
              <tr>
                <th @click="toggleSort('symbol')" class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase cursor-pointer hover:text-gray-700 select-none">
                  {{ t('common.symbol') }} <span class="text-gray-400">{{ sortIcon('symbol') }}</span>
                </th>
                <th @click="toggleSort('name')" class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase cursor-pointer hover:text-gray-700 select-none">
                  {{ t('common.name') }} <span class="text-gray-400">{{ sortIcon('name') }}</span>
                </th>
                <th @click="toggleSort('close')" class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase cursor-pointer hover:text-gray-700 select-none">
                  {{ t('table.close') }} <span class="text-gray-400">{{ sortIcon('close') }}</span>
                </th>
                <th @click="toggleSort('change_pct')" class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase cursor-pointer hover:text-gray-700 select-none">
                  {{ t('table.changePct') }} <span class="text-gray-400">{{ sortIcon('change_pct') }}</span>
                </th>
                <th @click="toggleSort('volume')" class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase cursor-pointer hover:text-gray-700 select-none">
                  {{ t('table.volume') }} <span class="text-gray-400">{{ sortIcon('volume') }}</span>
                </th>
                <th @click="toggleSort('time')" class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase cursor-pointer hover:text-gray-700 select-none">
                  {{ t('table.date') }} <span class="text-gray-400">{{ sortIcon('time') }}</span>
                </th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-200">
              <tr
                v-for="stock in stocks"
                :key="stock.symbol"
                @click="goToDetail(stock.symbol)"
                class="hover:bg-gray-50 cursor-pointer transition"
              >
                <td class="px-4 py-3 text-sm font-medium text-blue-600">{{ stock.symbol }}</td>
                <td class="px-4 py-3 text-sm text-gray-700">{{ stock.name || '-' }}</td>
                <td class="px-4 py-3 text-sm text-right font-mono">{{ stock.close.toFixed(2) }}</td>
                <td
                  class="px-4 py-3 text-sm text-right font-mono"
                  :class="stock.change_pct != null && stock.change_pct >= 0 ? 'text-red-600' : 'text-green-600'"
                >
                  {{ stock.change_pct != null ? stock.change_pct.toFixed(2) + '%' : '-' }}
                </td>
                <td class="px-4 py-3 text-sm text-right font-mono">
                  {{ stock.volume.toLocaleString() }}
                </td>
                <td class="px-4 py-3 text-sm text-right text-gray-500">
                  {{ stock.time.split('T')[0] }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Pagination -->
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between mt-4 gap-3 text-sm text-gray-600">
        <div class="flex items-center gap-3">
          <span>{{ t('table.total', { total }) }}</span>
          <span class="flex items-center gap-1">
            {{ t('table.pageSize') }}
            <select
              :value="pageSize"
              @change="changePageSize(Number(($event.target as HTMLSelectElement).value))"
              class="border border-gray-300 rounded px-2 py-1 text-sm"
            >
              <option v-for="s in pageSizeOptions" :key="s" :value="s">{{ s }}</option>
            </select>
            {{ t('table.items') }}
          </span>
        </div>
        <div class="flex items-center gap-2">
          <button
            @click="changePage(page - 1)"
            :disabled="page <= 1"
            class="px-3 py-1 rounded border border-gray-300 hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {{ t('table.prev') }}
          </button>
          <span class="px-2">{{ t('table.page', { page, pages: totalPages }) }}</span>
          <button
            @click="changePage(page + 1)"
            :disabled="page >= totalPages"
            class="px-3 py-1 rounded border border-gray-300 hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {{ t('table.next') }}
          </button>
        </div>
      </div>
    </template>
  </div>
</template>
