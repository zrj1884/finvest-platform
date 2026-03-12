<script setup lang="ts">
import { ref, watch } from 'vue'
import { searchSymbols, type SymbolItem } from '../api/market'

const props = defineProps<{
  modelValue: string
  market: string
  placeholder?: string
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
}>()

const query = ref(props.modelValue)
const suggestions = ref<SymbolItem[]>([])
const showDropdown = ref(false)
let debounceTimer: ReturnType<typeof setTimeout> | null = null

watch(
  () => props.modelValue,
  (v) => {
    if (v !== query.value) query.value = v
  },
)

function onInput() {
  emit('update:modelValue', query.value)
  if (debounceTimer) clearTimeout(debounceTimer)
  const q = query.value.trim()
  if (q.length < 1) {
    suggestions.value = []
    showDropdown.value = false
    return
  }
  debounceTimer = setTimeout(async () => {
    try {
      suggestions.value = await searchSymbols(q, props.market, 8)
      showDropdown.value = suggestions.value.length > 0
    } catch {
      suggestions.value = []
      showDropdown.value = false
    }
  }, 250)
}

function select(item: SymbolItem) {
  query.value = item.symbol
  emit('update:modelValue', item.symbol)
  showDropdown.value = false
}

function onBlur() {
  // Delay to allow click on suggestion
  setTimeout(() => {
    showDropdown.value = false
  }, 150)
}
</script>

<template>
  <div class="relative">
    <input
      v-model="query"
      @input="onInput"
      @focus="onInput"
      @blur="onBlur"
      type="text"
      :placeholder="placeholder"
      class="w-full border border-gray-300 rounded-md px-3 py-1.5 text-sm focus:ring-blue-500 focus:border-blue-500"
    />
    <div
      v-if="showDropdown"
      class="absolute z-50 w-full mt-1 bg-white border border-gray-200 rounded-md shadow-lg max-h-48 overflow-y-auto"
    >
      <button
        v-for="item in suggestions"
        :key="item.symbol"
        @mousedown.prevent="select(item)"
        class="w-full text-left px-3 py-1.5 text-sm hover:bg-blue-50 flex justify-between items-center"
      >
        <span class="font-mono font-medium text-gray-900">{{ item.symbol }}</span>
        <span class="text-xs text-gray-500 truncate ml-2">{{ item.name }}</span>
      </button>
    </div>
  </div>
</template>
