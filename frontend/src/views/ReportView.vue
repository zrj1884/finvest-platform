<script setup lang="ts">
import { ref } from 'vue'
import { generateStockReport, type ReportResponse } from '../api/ai'

const symbol = ref('')
const market = ref('a_share')
const report = ref<ReportResponse | null>(null)
const loading = ref(false)
const error = ref('')

const marketOptions = [
  { label: 'A-Share', value: 'a_share' },
  { label: 'US Stock', value: 'us_stock' },
  { label: 'HK Stock', value: 'hk_stock' },
]

async function generate() {
  if (!symbol.value.trim()) return
  loading.value = true
  error.value = ''
  report.value = null
  try {
    report.value = await generateStockReport(symbol.value.trim(), market.value)
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Failed to generate report. Check LLM API key configuration.'
  } finally {
    loading.value = false
  }
}

function formatMd(md: string): string {
  // Simple markdown to HTML: headings, bold, lists, paragraphs
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
    <h1 class="text-2xl font-bold text-gray-900 mb-6">AI Research Reports</h1>

    <!-- Generate form -->
    <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
      <div class="flex flex-col sm:flex-row gap-3">
        <select
          v-model="market"
          class="border border-gray-300 rounded-md px-3 py-2 text-sm focus:ring-blue-500 focus:border-blue-500"
        >
          <option v-for="opt in marketOptions" :key="opt.value" :value="opt.value">
            {{ opt.label }}
          </option>
        </select>
        <input
          v-model="symbol"
          @keyup.enter="generate"
          type="text"
          placeholder="Enter stock symbol..."
          class="border border-gray-300 rounded-md px-3 py-2 text-sm focus:ring-blue-500 focus:border-blue-500 flex-1"
        />
        <button
          @click="generate"
          :disabled="loading || !symbol.trim()"
          class="bg-blue-600 text-white px-6 py-2 rounded-md text-sm hover:bg-blue-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {{ loading ? 'Generating...' : 'Generate Report' }}
        </button>
      </div>
      <p class="text-xs text-gray-500 mt-2">
        Requires LLM API key (DeepSeek/Qwen/OpenAI) configured in backend .env
      </p>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="text-center py-12">
      <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      <p class="text-gray-500 mt-4">Analyzing data and generating report...</p>
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
          {{ report.tokens_used }} tokens · ${{ report.cost_usd.toFixed(4) }}
        </div>
      </div>
      <div class="prose max-w-none text-gray-700 leading-relaxed" v-html="formatMd(report.content_md)"></div>
      <div class="mt-6 pt-4 border-t border-gray-200 text-xs text-gray-400">
        Generated at {{ report.generated_at.split('T')[0] }}
      </div>
    </div>

    <!-- Empty state -->
    <div v-if="!loading && !report && !error" class="text-center py-12 text-gray-500">
      Enter a stock symbol above to generate an AI research report.
    </div>
  </div>
</template>
