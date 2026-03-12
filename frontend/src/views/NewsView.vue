<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { getNews, type NewsArticle } from '../api/market'

const { t, locale } = useI18n()

const news = ref<NewsArticle[]>([])
const loading = ref(false)
const selectedSource = ref<string>('')
const searchKeyword = ref('')
let debounceTimer: ReturnType<typeof setTimeout> | null = null

const sources = [
  { value: '', key: 'news.allSources' },
  { value: 'sina_finance', key: 'news.sinaFinance' },
  { value: 'eastmoney', key: 'news.eastMoney' },
  { value: 'xueqiu', key: 'news.xueqiu' },
]

async function loadData() {
  loading.value = true
  try {
    news.value = await getNews(
      50,
      selectedSource.value || undefined,
      undefined,
      searchKeyword.value.trim() || undefined,
    )
  } catch {
    news.value = []
  } finally {
    loading.value = false
  }
}

function onSearchInput() {
  if (debounceTimer) clearTimeout(debounceTimer)
  debounceTimer = setTimeout(loadData, 400)
}

function formatTime(iso: string): string {
  const d = new Date(iso)
  const loc = locale.value === 'zh' ? 'zh-CN' : 'en-US'
  return d.toLocaleString(loc, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

function sourceLabel(source: string): string {
  const found = sources.find((s) => s.value === source)
  return found ? t(found.key) : source
}

onMounted(loadData)
watch(selectedSource, loadData)
</script>

<template>
  <div>
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6 gap-3">
      <h1 class="text-2xl font-bold text-gray-900">{{ t('news.title') }}</h1>
      <div class="flex gap-2">
        <input
          v-model="searchKeyword"
          @input="onSearchInput"
          type="text"
          :placeholder="t('news.searchPlaceholder')"
          class="border border-gray-300 rounded-md px-3 py-1.5 text-sm focus:ring-blue-500 focus:border-blue-500 w-48"
        />
        <select
          v-model="selectedSource"
          class="border border-gray-300 rounded-md px-3 py-1.5 text-sm focus:ring-blue-500 focus:border-blue-500"
        >
          <option v-for="s in sources" :key="s.value" :value="s.value">{{ t(s.key) }}</option>
        </select>
      </div>
    </div>

    <div v-if="loading" class="text-center py-12 text-gray-500">{{ t('common.loading') }}</div>

    <div v-else-if="news.length === 0" class="text-center py-12 text-gray-500">
      {{ t('news.noArticles') }}
    </div>

    <div v-else class="space-y-3">
      <a
        v-for="(article, idx) in news"
        :key="idx"
        :href="article.url"
        target="_blank"
        rel="noopener noreferrer"
        class="block bg-white rounded-lg shadow-sm border border-gray-200 p-4 hover:shadow-md transition"
      >
        <div class="flex items-start justify-between">
          <h3 class="text-sm font-medium text-gray-900 flex-1 mr-3">{{ article.title }}</h3>
          <span class="text-xs text-gray-400 whitespace-nowrap">{{ formatTime(article.time) }}</span>
        </div>
        <p v-if="article.content" class="mt-1 text-xs text-gray-500 line-clamp-2">
          {{ article.content }}
        </p>
        <div class="mt-2 flex items-center gap-2">
          <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-600">
            {{ sourceLabel(article.source) }}
          </span>
          <span
            v-if="article.symbols"
            class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-50 text-blue-600"
          >
            {{ article.symbols }}
          </span>
          <span
            v-if="article.sentiment_score != null"
            class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium"
            :class="article.sentiment_score >= 0 ? 'bg-green-50 text-green-600' : 'bg-red-50 text-red-600'"
          >
            {{ t('news.sentiment') }}: {{ article.sentiment_score.toFixed(2) }}
          </span>
        </div>
      </a>
    </div>
  </div>
</template>
