<script setup lang="ts">
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
</script>

<template>
  <div>
    <h1 class="text-2xl font-bold text-gray-900 mb-6">{{ t('home.title') }}</h1>

    <!-- Market overview cards -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
      <router-link
        to="/market/a_share"
        class="bg-white rounded-lg shadow-sm border border-gray-200 p-5 hover:shadow-md transition"
      >
        <h3 class="text-sm font-medium text-gray-500">{{ t('home.aShare.subtitle') }}</h3>
        <p class="mt-1 text-lg font-semibold text-gray-900">{{ t('home.aShare.name') }}</p>
        <p class="mt-1 text-sm text-gray-500">{{ t('home.aShare.desc') }}</p>
      </router-link>

      <router-link
        to="/market/us_stock"
        class="bg-white rounded-lg shadow-sm border border-gray-200 p-5 hover:shadow-md transition"
      >
        <h3 class="text-sm font-medium text-gray-500">{{ t('home.usStock.subtitle') }}</h3>
        <p class="mt-1 text-lg font-semibold text-gray-900">{{ t('home.usStock.name') }}</p>
        <p class="mt-1 text-sm text-gray-500">{{ t('home.usStock.desc') }}</p>
      </router-link>

      <router-link
        to="/market/hk_stock"
        class="bg-white rounded-lg shadow-sm border border-gray-200 p-5 hover:shadow-md transition"
      >
        <h3 class="text-sm font-medium text-gray-500">{{ t('home.hkStock.subtitle') }}</h3>
        <p class="mt-1 text-lg font-semibold text-gray-900">{{ t('home.hkStock.name') }}</p>
        <p class="mt-1 text-sm text-gray-500">{{ t('home.hkStock.desc') }}</p>
      </router-link>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
      <router-link
        to="/fund"
        class="bg-white rounded-lg shadow-sm border border-gray-200 p-5 hover:shadow-md transition"
      >
        <h3 class="text-sm font-medium text-gray-500">{{ t('home.fund.subtitle') }}</h3>
        <p class="mt-1 text-lg font-semibold text-gray-900">{{ t('home.fund.name') }}</p>
        <p class="mt-1 text-sm text-gray-500">{{ t('home.fund.desc') }}</p>
      </router-link>

      <router-link
        to="/bond"
        class="bg-white rounded-lg shadow-sm border border-gray-200 p-5 hover:shadow-md transition"
      >
        <h3 class="text-sm font-medium text-gray-500">{{ t('home.bond.subtitle') }}</h3>
        <p class="mt-1 text-lg font-semibold text-gray-900">{{ t('home.bond.name') }}</p>
        <p class="mt-1 text-sm text-gray-500">{{ t('home.bond.desc') }}</p>
      </router-link>

      <router-link
        to="/news"
        class="bg-white rounded-lg shadow-sm border border-gray-200 p-5 hover:shadow-md transition"
      >
        <h3 class="text-sm font-medium text-gray-500">{{ t('home.news.subtitle') }}</h3>
        <p class="mt-1 text-lg font-semibold text-gray-900">{{ t('home.news.name') }}</p>
        <p class="mt-1 text-sm text-gray-500">{{ t('home.news.desc') }}</p>
      </router-link>
    </div>
  </div>
</template>
