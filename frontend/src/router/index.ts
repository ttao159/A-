import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('../views/LoginView.vue'),
      meta: { title: '登录', guest: true },
    },
    {
      path: '/',
      name: 'home',
      component: () => import('../views/HomeView.vue'),
      meta: { title: '账户' },
    },
    {
      path: '/strategy',
      name: 'strategy-center',
      component: () => import('../views/StrategyCenterView.vue'),
      meta: { title: '策略中心' },
      children: [
        {
          path: '',
          name: 'strategy',
          component: () => import('../views/StrategyView.vue'),
          meta: { title: '策略' },
        },
        {
          path: 'backtest',
          name: 'backtest',
          component: () => import('../views/BacktestView.vue'),
          meta: { title: '回测' },
        },
        {
          path: 'screener',
          name: 'screener',
          component: () => import('../views/ScreenerView.vue'),
          meta: { title: '选股' },
        },
        {
          path: 'scan',
          name: 'scan',
          component: () => import('../views/GeneratorView.vue'),
          meta: { title: '扫描' },
        },
      ],
    },
    {
      path: '/trade',
      name: 'trade',
      component: () => import('../views/TradeView.vue'),
      meta: { title: '交易' },
    },
    {
      path: '/about',
      name: 'about',
      component: () => import('../views/AboutView.vue'),
      meta: { title: '说明' },
    },
    {
      path: '/stock/:code',
      name: 'stock',
      component: () => import('../views/StockDetail.vue'),
      meta: { title: '个股' },
    },
    {
      path: '/alerts',
      name: 'alerts',
      component: () => import('../views/AlertsView.vue'),
      meta: { title: '预警' },
    },
    {
      path: '/settings',
      name: 'settings',
      component: () => import('../views/SettingsView.vue'),
      meta: { title: '个人中心' },
    },
    { path: '/backtest', redirect: '/strategy/backtest' },
    { path: '/screener', redirect: '/strategy/screener' },
    { path: '/generator', redirect: '/strategy/scan' },
  ],
})

// 路由守卫：未登录重定向到登录页
router.beforeEach((to) => {
  const token = localStorage.getItem('token')
  const isGuest = to.meta.guest as boolean
  
  if (!token && !isGuest) {
    return '/login'
  }
  
  if (token && isGuest) {
    return '/'
  }
})

export default router
