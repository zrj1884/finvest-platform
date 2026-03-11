<script setup lang="ts">
</script>

<template>
  <div>
    <h1 class="text-2xl font-bold text-gray-900 mb-6">Dashboard</h1>

    <!-- Market overview cards -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
      <router-link
        to="/market/a_share"
        class="bg-white rounded-lg shadow-sm border border-gray-200 p-5 hover:shadow-md transition"
      >
        <h3 class="text-sm font-medium text-gray-500">A-Share Market</h3>
        <p class="mt-1 text-lg font-semibold text-gray-900">Shanghai / Shenzhen</p>
        <p class="mt-1 text-sm text-gray-500">A stock daily data, realtime quotes</p>
      </router-link>

      <router-link
        to="/market/us_stock"
        class="bg-white rounded-lg shadow-sm border border-gray-200 p-5 hover:shadow-md transition"
      >
        <h3 class="text-sm font-medium text-gray-500">US Stock Market</h3>
        <p class="mt-1 text-lg font-semibold text-gray-900">NYSE / NASDAQ</p>
        <p class="mt-1 text-sm text-gray-500">US equity daily data via yfinance</p>
      </router-link>

      <router-link
        to="/market/hk_stock"
        class="bg-white rounded-lg shadow-sm border border-gray-200 p-5 hover:shadow-md transition"
      >
        <h3 class="text-sm font-medium text-gray-500">HK Stock Market</h3>
        <p class="mt-1 text-lg font-semibold text-gray-900">HKEX</p>
        <p class="mt-1 text-sm text-gray-500">Hong Kong stock daily data</p>
      </router-link>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
      <router-link
        to="/fund"
        class="bg-white rounded-lg shadow-sm border border-gray-200 p-5 hover:shadow-md transition"
      >
        <h3 class="text-sm font-medium text-gray-500">Funds</h3>
        <p class="mt-1 text-lg font-semibold text-gray-900">Open-End Funds</p>
        <p class="mt-1 text-sm text-gray-500">Fund NAV history and tracking</p>
      </router-link>

      <router-link
        to="/bond"
        class="bg-white rounded-lg shadow-sm border border-gray-200 p-5 hover:shadow-md transition"
      >
        <h3 class="text-sm font-medium text-gray-500">Bonds</h3>
        <p class="mt-1 text-lg font-semibold text-gray-900">Convertible Bonds</p>
        <p class="mt-1 text-sm text-gray-500">Bond daily data and yields</p>
      </router-link>

      <router-link
        to="/news"
        class="bg-white rounded-lg shadow-sm border border-gray-200 p-5 hover:shadow-md transition"
      >
        <h3 class="text-sm font-medium text-gray-500">News</h3>
        <p class="mt-1 text-lg font-semibold text-gray-900">Financial News Feed</p>
        <p class="mt-1 text-sm text-gray-500">Sina Finance, East Money, Xueqiu</p>
      </router-link>
    </div>
  </div>
</template>
