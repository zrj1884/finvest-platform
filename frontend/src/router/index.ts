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
        path: 'fund/:symbol',
        name: 'FundDetail',
        component: () => import('../views/FundDetailView.vue'),
      },
      {
        path: 'bond',
        name: 'Bond',
        component: () => import('../views/BondView.vue'),
      },
      {
        path: 'bond/:symbol',
        name: 'BondDetail',
        component: () => import('../views/BondDetailView.vue'),
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
      {
        path: 'trading',
        name: 'Trading',
        component: () => import('../views/TradingView.vue'),
      },
      {
        path: 'portfolio',
        name: 'Portfolio',
        component: () => import('../views/PortfolioView.vue'),
      },
      {
        path: 'accounts',
        name: 'Accounts',
        component: () => import('../views/AccountsView.vue'),
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
