import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'home',
      component: () => import('../views/HomeView.vue'),
    },
    {
      path: '/strategy',
      name: 'strategy',
      component: () => import('../views/StrategyView.vue'),
    },
    {
      path: '/backtest',
      name: 'backtest',
      component: () => import('../views/BacktestView.vue'),
    },
    {
      path: '/trade',
      name: 'trade',
      component: () => import('../views/TradeView.vue'),
    },
    {
      path: '/generator',
      name: 'generator',
      component: () => import('../views/GeneratorView.vue'),
    },
    {
      path: '/about',
      name: 'about',
      component: () => import('../views/AboutView.vue'),
    },
    {
      path: '/stock/:code',
      name: 'stock',
      component: () => import('../views/StockDetail.vue'),
    },
  ],
})

export default router
