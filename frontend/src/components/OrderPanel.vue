<script setup lang="ts">
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { placeOrder, type OrderCreateRequest } from '../api/trading'
import SymbolAutocomplete from './SymbolAutocomplete.vue'

const { t } = useI18n()

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

function lotSize(): number {
  if (props.market === 'bond') return 10
  if (props.market === 'a_share' || props.market === 'fund') return 100
  return 1
}

async function submit() {
  error.value = ''
  success.value = ''
  if (!symbol.value.trim()) {
    error.value = t('trading.symbolRequired')
    return
  }
  if (!quantity.value || quantity.value <= 0) {
    error.value = t('trading.qtyRequired')
    return
  }
  const lot = lotSize()
  if (side.value === 'buy' && lot > 1 && quantity.value % lot !== 0) {
    error.value = t('trading.lotSizeError', { lot })
    return
  }
  if (isLimit.value && !price.value) {
    error.value = t('trading.priceRequired')
    return
  }
  if (isLimit.value && price.value && price.value <= 0) {
    error.value = t('trading.priceRequired')
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
    // Reset form after success
    symbol.value = ''
    price.value = undefined
    emit('orderPlaced')
  } catch (e: any) {
    error.value = e.response?.data?.detail || t('trading.orderFailed')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
    <h3 class="text-sm font-bold text-gray-900 mb-3">{{ t('trading.placeOrder') }}</h3>

    <!-- Side toggle -->
    <div class="flex gap-2 mb-3">
      <button
        @click="side = 'buy'"
        :class="[
          'flex-1 py-1.5 text-sm font-medium rounded-md transition',
          side === 'buy' ? 'bg-red-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200',
        ]"
      >
        {{ t('common.buy') }}
      </button>
      <button
        @click="side = 'sell'"
        :class="[
          'flex-1 py-1.5 text-sm font-medium rounded-md transition',
          side === 'sell' ? 'bg-green-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200',
        ]"
      >
        {{ t('common.sell') }}
      </button>
    </div>

    <!-- Symbol -->
    <div class="mb-3">
      <label class="block text-xs text-gray-500 mb-1">{{ t('common.symbol') }}</label>
      <SymbolAutocomplete
        v-model="symbol"
        :market="market"
        :placeholder="t('trading.symbolPlaceholder')"
      />
    </div>

    <!-- Order type -->
    <div class="mb-3">
      <label class="block text-xs text-gray-500 mb-1">{{ t('common.type') }}</label>
      <select
        v-model="orderType"
        class="w-full border border-gray-300 rounded-md px-3 py-1.5 text-sm focus:ring-blue-500 focus:border-blue-500"
      >
        <option value="market">{{ t('trading.marketOrder') }}</option>
        <option value="limit">{{ t('trading.limitOrder') }}</option>
      </select>
    </div>

    <!-- Quantity -->
    <div class="mb-3">
      <label class="block text-xs text-gray-500 mb-1">{{ t('common.quantity') }}</label>
      <input
        v-model.number="quantity"
        type="number"
        min="1"
        class="w-full border border-gray-300 rounded-md px-3 py-1.5 text-sm focus:ring-blue-500 focus:border-blue-500"
      />
    </div>

    <!-- Price (limit only) -->
    <div v-if="isLimit" class="mb-3">
      <label class="block text-xs text-gray-500 mb-1">{{ t('common.price') }}</label>
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
      {{ loading ? t('trading.submitting') : side === 'buy' ? t('common.buy') : t('common.sell') }}
    </button>
  </div>
</template>
