<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { getNews, type NewsArticle } from '../api/market'

const articles = ref<NewsArticle[]>([])
const loading = ref(false)

async function loadData() {
  loading.value = true
  try {
    articles.value = await getNews(100)
  } catch {
    // ignore
  } finally {
    loading.value = false
  }
}

const scored = computed(() => articles.value.filter((a) => a.sentiment_score != null))
const avgSentiment = computed(() => {
  if (scored.value.length === 0) return 0
  return scored.value.reduce((s, a) => s + (a.sentiment_score ?? 0), 0) / scored.value.length
})
const bullish = computed(() => scored.value.filter((a) => (a.sentiment_score ?? 0) > 0.2).length)
const bearish = computed(() => scored.value.filter((a) => (a.sentiment_score ?? 0) < -0.2).length)
const neutral = computed(() => scored.value.length - bullish.value - bearish.value)

function sentimentColor(score: number | null): string {
  if (score == null) return 'text-gray-400'
  if (score > 0.2) return 'text-red-600'
  if (score < -0.2) return 'text-green-600'
  return 'text-gray-500'
}

function sentimentLabel(score: number | null): string {
  if (score == null) return 'N/A'
  if (score > 0.5) return 'Very Bullish'
  if (score > 0.2) return 'Bullish'
  if (score < -0.5) return 'Very Bearish'
  if (score < -0.2) return 'Bearish'
  return 'Neutral'
}

onMounted(loadData)
</script>

<template>
  <div>
    <h1 class="text-2xl font-bold text-gray-900 mb-6">Market Sentiment</h1>

    <!-- Summary cards -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
      <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <p class="text-xs text-gray-500">Average Sentiment</p>
        <p class="text-2xl font-mono font-bold" :class="sentimentColor(avgSentiment)">
          {{ avgSentiment.toFixed(2) }}
        </p>
        <p class="text-xs" :class="sentimentColor(avgSentiment)">{{ sentimentLabel(avgSentiment) }}</p>
      </div>
      <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <p class="text-xs text-gray-500">Bullish Articles</p>
        <p class="text-2xl font-mono font-bold text-red-600">{{ bullish }}</p>
      </div>
      <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <p class="text-xs text-gray-500">Bearish Articles</p>
        <p class="text-2xl font-mono font-bold text-green-600">{{ bearish }}</p>
      </div>
      <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <p class="text-xs text-gray-500">Neutral / Unscored</p>
        <p class="text-2xl font-mono font-bold text-gray-500">
          {{ neutral }} / {{ articles.length - scored.length }}
        </p>
      </div>
    </div>

    <!-- Sentiment distribution bar -->
    <div v-if="scored.length > 0" class="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-6">
      <p class="text-sm font-medium text-gray-700 mb-2">Sentiment Distribution</p>
      <div class="flex h-6 rounded-full overflow-hidden">
        <div
          class="bg-red-500"
          :style="{ width: `${(bullish / scored.length) * 100}%` }"
        ></div>
        <div
          class="bg-gray-300"
          :style="{ width: `${(neutral / scored.length) * 100}%` }"
        ></div>
        <div
          class="bg-green-500"
          :style="{ width: `${(bearish / scored.length) * 100}%` }"
        ></div>
      </div>
      <div class="flex justify-between text-xs text-gray-500 mt-1">
        <span>Bullish {{ Math.round((bullish / scored.length) * 100) }}%</span>
        <span>Neutral {{ Math.round((neutral / scored.length) * 100) }}%</span>
        <span>Bearish {{ Math.round((bearish / scored.length) * 100) }}%</span>
      </div>
    </div>

    <!-- Article list with sentiment scores -->
    <div v-if="loading" class="text-center py-12 text-gray-500">Loading...</div>
    <div v-else-if="articles.length === 0" class="text-center py-12 text-gray-500">
      No news articles available.
    </div>
    <div v-else class="space-y-2">
      <div
        v-for="article in articles"
        :key="article.url"
        class="bg-white rounded-lg shadow-sm border border-gray-200 p-4 flex items-start gap-4"
      >
        <div class="flex-1 min-w-0">
          <a
            :href="article.url"
            target="_blank"
            rel="noopener"
            class="text-sm font-medium text-gray-900 hover:text-blue-600 line-clamp-2"
          >
            {{ article.title }}
          </a>
          <div class="flex items-center gap-3 mt-1 text-xs text-gray-500">
            <span>{{ article.source }}</span>
            <span>{{ article.time.split('T')[0] }}</span>
          </div>
        </div>
        <div class="flex-shrink-0 text-right">
          <p class="text-sm font-mono font-bold" :class="sentimentColor(article.sentiment_score)">
            {{ article.sentiment_score != null ? article.sentiment_score.toFixed(2) : '-' }}
          </p>
          <p class="text-xs" :class="sentimentColor(article.sentiment_score)">
            {{ sentimentLabel(article.sentiment_score) }}
          </p>
        </div>
      </div>
    </div>
  </div>
</template>
