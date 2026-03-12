<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { generateStockReport, type ReportResponse } from '../api/ai'

const { t } = useI18n()

const symbol = ref('')
const market = ref('a_share')
const report = ref<ReportResponse | null>(null)
const loading = ref(false)
const error = ref('')

const marketOptions = [
  { key: 'market.a_share', value: 'a_share' },
  { key: 'market.us_stock', value: 'us_stock' },
  { key: 'market.hk_stock', value: 'hk_stock' },
]

async function generate() {
  if (!symbol.value.trim()) return
  loading.value = true
  error.value = ''
  report.value = null
  try {
    report.value = await generateStockReport(symbol.value.trim(), market.value)
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : t('report.generateFailed')
  } finally {
    loading.value = false
  }
}

function formatMd(md: string): string {
  return md
    .replace(/^### (.+)$/gm, '<h3 class="text-lg font-semibold mt-4 mb-2">$1</h3>')
    .replace(/^## (.+)$/gm, '<h2 class="text-xl font-bold mt-6 mb-3">$1</h2>')
    .replace(/^# (.+)$/gm, '<h1 class="text-2xl font-bold mt-6 mb-3">$1</h1>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/^- (.+)$/gm, '<li class="ml-4">$1</li>')
    .replace(/\n{2,}/g, '<br/><br/>')
}
</script>

<template>
  <div>
    <h1 class="text-2xl font-bold text-gray-900 mb-6">{{ t('report.title') }}</h1>

    <!-- Generate form -->
    <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
      <div class="flex flex-col sm:flex-row gap-3">
        <select
          v-model="market"
          class="border border-gray-300 rounded-md px-3 py-2 text-sm focus:ring-blue-500 focus:border-blue-500"
        >
          <option v-for="opt in marketOptions" :key="opt.value" :value="opt.value">
            {{ t(opt.key) }}
          </option>
        </select>
        <input
          v-model="symbol"
          @keyup.enter="generate"
          type="text"
          :placeholder="t('report.symbolPlaceholder')"
          class="border border-gray-300 rounded-md px-3 py-2 text-sm focus:ring-blue-500 focus:border-blue-500 flex-1"
        />
        <button
          @click="generate"
          :disabled="loading || !symbol.trim()"
          class="bg-blue-600 text-white px-6 py-2 rounded-md text-sm hover:bg-blue-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {{ loading ? t('detail.generating') : t('detail.generateReport') }}
        </button>
      </div>
      <p class="text-xs text-gray-500 mt-2">
        {{ t('report.apiHint') }}
      </p>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="text-center py-12">
      <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      <p class="text-gray-500 mt-4">{{ t('report.analyzingData') }}</p>
    </div>

    <!-- Error -->
    <div v-if="error" class="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
      <p class="text-red-700 text-sm">{{ error }}</p>
    </div>

    <!-- Report -->
    <div v-if="report" class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-xl font-bold text-gray-900">{{ report.title }}</h2>
        <div class="text-xs text-gray-400">
          {{ report.tokens_used }} {{ t('report.tokens') }} · ${{ report.cost_usd.toFixed(4) }}
        </div>
      </div>
      <div class="prose max-w-none text-gray-700 leading-relaxed" v-html="formatMd(report.content_md)"></div>
      <div class="mt-6 pt-4 border-t border-gray-200 text-xs text-gray-400">
        {{ t('report.generatedAt') }} {{ report.generated_at.split('T')[0] }}
      </div>
    </div>

    <!-- Empty state -->
    <div v-if="!loading && !report && !error" class="text-center py-12 text-gray-500">
      {{ t('report.emptyHint') }}
    </div>
  </div>
</template>
