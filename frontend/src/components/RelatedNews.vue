<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { getNews, type NewsArticle } from '../api/market'

const props = defineProps<{
  keyword: string
}>()

const articles = ref<NewsArticle[]>([])
const loading = ref(false)

async function loadNews() {
  if (!props.keyword) return
  loading.value = true
  try {
    articles.value = await getNews(5, undefined, undefined, props.keyword)
  } catch {
    articles.value = []
  } finally {
    loading.value = false
  }
}

function formatTime(iso: string): string {
  const d = new Date(iso)
  return d.toLocaleString('zh-CN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

onMounted(loadNews)
watch(() => props.keyword, loadNews)
</script>

<template>
  <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
    <h2 class="text-lg font-bold text-gray-900 mb-4">Related News</h2>
    <div v-if="loading" class="text-center py-4 text-gray-500 text-sm">Loading...</div>
    <div v-else-if="articles.length === 0" class="text-center py-4 text-gray-400 text-sm">
      No related news found
    </div>
    <div v-else class="space-y-3">
      <a
        v-for="(article, idx) in articles"
        :key="idx"
        :href="article.url"
        target="_blank"
        rel="noopener noreferrer"
        class="block p-3 rounded-md hover:bg-gray-50 transition -mx-1"
      >
        <div class="flex items-start justify-between">
          <h3 class="text-sm font-medium text-gray-900 flex-1 mr-3 line-clamp-1">{{ article.title }}</h3>
          <span class="text-xs text-gray-400 whitespace-nowrap">{{ formatTime(article.time) }}</span>
        </div>
        <p v-if="article.content" class="mt-0.5 text-xs text-gray-500 line-clamp-1">{{ article.content }}</p>
      </a>
    </div>
  </div>
</template>
