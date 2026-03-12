import { createRouter, createWebHistory } from 'vue-router'
import AppLayout from '../components/AppLayout.vue'
import HomeView from '../views/HomeView.vue'

// Pages that require authentication
const AUTH_REQUIRED = new Set(['Trading', 'Portfolio', 'Accounts'])

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/LoginView.vue'),
  },
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

// Navigation guard: redirect to login for protected pages
router.beforeEach((to) => {
  if (AUTH_REQUIRED.has(to.name as string)) {
    const token = localStorage.getItem('access_token')
    const refreshTokenVal = localStorage.getItem('refresh_token')
    if (!token && !refreshTokenVal) {
      return { name: 'Login', query: { redirect: to.fullPath } }
    }
  }
})

export default router
