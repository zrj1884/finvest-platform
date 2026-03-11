<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getBondDaily, type BondDaily } from '../api/market'

const bonds = ref<BondDaily[]>([])
const loading = ref(false)

const defaultBonds = ['113050', '127045', '123136', '113648', '128108']

async function loadData() {
  loading.value = true
  bonds.value = []
  try {
    const results = await Promise.all(
      defaultBonds.map((s) => getBondDaily(s, 1).catch(() => [] as BondDaily[])),
    )
    bonds.value = results.flat()
  } catch {
    // ignore
  } finally {
    loading.value = false
  }
}

onMounted(loadData)
</script>

<template>
  <div>
    <h1 class="text-2xl font-bold text-gray-900 mb-6">Bonds</h1>

    <div v-if="loading" class="text-center py-12 text-gray-500">Loading...</div>
    <div v-else-if="bonds.length === 0" class="text-center py-12 text-gray-500">
      No bond data available.
    </div>
    <div v-else class="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
      <div class="overflow-x-auto">
        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-50">
            <tr>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Code</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Name</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
              <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Close</th>
              <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Change %</th>
              <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Volume</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-200">
            <tr v-for="bond in bonds" :key="bond.symbol" class="hover:bg-gray-50">
              <td class="px-4 py-3 text-sm font-medium text-blue-600">{{ bond.symbol }}</td>
              <td class="px-4 py-3 text-sm text-gray-700">{{ bond.name || '-' }}</td>
              <td class="px-4 py-3 text-sm text-gray-500">{{ bond.bond_type || '-' }}</td>
              <td class="px-4 py-3 text-sm text-right font-mono">{{ bond.close.toFixed(2) }}</td>
              <td
                class="px-4 py-3 text-sm text-right font-mono"
                :class="bond.change_pct != null && bond.change_pct >= 0 ? 'text-red-600' : 'text-green-600'"
              >
                {{ bond.change_pct != null ? bond.change_pct.toFixed(2) + '%' : '-' }}
              </td>
              <td class="px-4 py-3 text-sm text-right font-mono">
                {{ bond.volume.toLocaleString() }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
