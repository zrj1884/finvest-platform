<script setup lang="ts">
import { ref, computed } from 'vue'
import { placeOrder, type OrderCreateRequest } from '../api/trading'

const props = defineProps<{
  accountId: string
  market: string
}>()

const emit = defineEmits<{
  (e: 'orderPlaced'): void
}>()

const symbol = ref('')
const side = ref<'buy' | 'sell'>('buy')
const orderType = ref<'market' | 'limit'>('market')
const quantity = ref<number>(100)
const price = ref<number | undefined>(undefined)
const loading = ref(false)
const error = ref('')
const success = ref('')

const isLimit = computed(() => orderType.value === 'limit')

async function submit() {
  error.value = ''
  success.value = ''
  if (!symbol.value.trim()) {
    error.value = 'Symbol is required'
    return
  }
  if (isLimit.value && !price.value) {
    error.value = 'Price is required for limit orders'
    return
  }

  loading.value = true
  try {
    const req: OrderCreateRequest = {
      account_id: props.accountId,
      symbol: symbol.value.trim().toUpperCase(),
      side: side.value,
      order_type: orderType.value,
      quantity: quantity.value,
    }
    if (isLimit.value && price.value) {
      req.price = price.value
    }
    const order = await placeOrder(req)
    success.value = `Order ${order.status}: ${order.side} ${order.filled_quantity || order.quantity} ${order.symbol}`
    emit('orderPlaced')
  } catch (e: any) {
    error.value = e.response?.data?.detail || 'Failed to place order'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
    <h3 class="text-sm font-bold text-gray-900 mb-3">Place Order</h3>

    <!-- Side toggle -->
    <div class="flex gap-2 mb-3">
      <button
        @click="side = 'buy'"
        :class="[
          'flex-1 py-1.5 text-sm font-medium rounded-md transition',
          side === 'buy' ? 'bg-red-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200',
        ]"
      >
        Buy
      </button>
      <button
        @click="side = 'sell'"
        :class="[
          'flex-1 py-1.5 text-sm font-medium rounded-md transition',
          side === 'sell' ? 'bg-green-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200',
        ]"
      >
        Sell
      </button>
    </div>

    <!-- Symbol -->
    <div class="mb-3">
      <label class="block text-xs text-gray-500 mb-1">Symbol</label>
      <input
        v-model="symbol"
        type="text"
        placeholder="e.g. 600519"
        class="w-full border border-gray-300 rounded-md px-3 py-1.5 text-sm focus:ring-blue-500 focus:border-blue-500"
      />
    </div>

    <!-- Order type -->
    <div class="mb-3">
      <label class="block text-xs text-gray-500 mb-1">Type</label>
      <select
        v-model="orderType"
        class="w-full border border-gray-300 rounded-md px-3 py-1.5 text-sm focus:ring-blue-500 focus:border-blue-500"
      >
        <option value="market">Market</option>
        <option value="limit">Limit</option>
      </select>
    </div>

    <!-- Quantity -->
    <div class="mb-3">
      <label class="block text-xs text-gray-500 mb-1">Quantity</label>
      <input
        v-model.number="quantity"
        type="number"
        min="1"
        class="w-full border border-gray-300 rounded-md px-3 py-1.5 text-sm focus:ring-blue-500 focus:border-blue-500"
      />
    </div>

    <!-- Price (limit only) -->
    <div v-if="isLimit" class="mb-3">
      <label class="block text-xs text-gray-500 mb-1">Price</label>
      <input
        v-model.number="price"
        type="number"
        step="0.01"
        min="0.01"
        class="w-full border border-gray-300 rounded-md px-3 py-1.5 text-sm focus:ring-blue-500 focus:border-blue-500"
      />
    </div>

    <!-- Error / Success -->
    <div v-if="error" class="mb-3 text-xs text-red-600 bg-red-50 rounded p-2">{{ error }}</div>
    <div v-if="success" class="mb-3 text-xs text-green-600 bg-green-50 rounded p-2">{{ success }}</div>

    <!-- Submit -->
    <button
      @click="submit"
      :disabled="loading"
      :class="[
        'w-full py-2 text-sm font-medium rounded-md transition disabled:opacity-50',
        side === 'buy'
          ? 'bg-red-600 text-white hover:bg-red-700'
          : 'bg-green-600 text-white hover:bg-green-700',
      ]"
    >
      {{ loading ? 'Submitting...' : side === 'buy' ? 'Buy' : 'Sell' }}
    </button>
  </div>
</template>
