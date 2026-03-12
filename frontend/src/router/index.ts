import { createRouter, createWebHistory } from 'vue-router'
import AppLayout from '../components/AppLayout.vue'
import HomeView from '../views/HomeView.vue'

const routes = [
  {
    path: '/',
    component: AppLayout,
    children: [
      { path: '', name: 'Home', component: HomeView },
      {
        path: 'market/:market',
        name: 'Market',
        component: () => import('../views/MarketView.vue'),
      },
      {
        path: 'stock/:market/:symbol',
        name: 'StockDetail',
        component: () => import('../views/StockDetailView.vue'),
      },
      {
        path: 'fund',
        name: 'Fund',
        component: () => import('../views/FundView.vue'),
      },
      {
        path: 'bond',
        name: 'Bond',
        component: () => import('../views/BondView.vue'),
      },
      {
        path: 'news',
        name: 'News',
        component: () => import('../views/NewsView.vue'),
      },
      {
        path: 'report',
        name: 'Report',
        component: () => import('../views/ReportView.vue'),
      },
      {
        path: 'sentiment',
        name: 'Sentiment',
        component: () => import('../views/SentimentView.vue'),
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
