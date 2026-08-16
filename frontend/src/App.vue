<template>
  <div class="app">
    <header class="app-header">
      <h1>{{ title }}</h1>
      <div class="header-right">
        <button class="theme-btn" @click="toggleTheme" aria-label="切换主题">
          <Icon :name="isDark ? 'sun' : 'moon'" :size="18" />
        </button>
        <span v-if="accountStore.isLive" class="badge live">实盘</span>
        <span v-else class="badge paper">模拟盘</span>
      </div>
    </header>
    <div v-if="accountStore.isLive" class="risk-banner">
      实盘交易存在风险，请谨慎操作并核实每笔委托
    </div>
    <div class="ptr-indicator" :style="{ height: pullH + 'px' }">
      <span v-if="refreshing">刷新中...</span>
      <span v-else-if="pullH >= THRESHOLD">释放刷新</span>
      <span v-else>下拉刷新</span>
    </div>
    <main
      ref="mainRef"
      class="app-main"
      @touchstart="onTouchStart"
      @touchmove="onTouchMove"
      @touchend="onTouchEnd"
    >
      <router-view v-slot="{ Component }">
        <Transition name="page" mode="out-in">
          <component :is="Component" />
        </Transition>
      </router-view>
    </main>
    <nav class="tab-bar">
      <router-link v-for="tab in tabs" :key="tab.path" :to="tab.path" class="tab-item">
        <Icon :name="tab.iconName" :size="22" />
        <span class="tab-label">{{ tab.label }}</span>
      </router-link>
    </nav>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { useAccountStore } from './stores/account'
import { triggerPullRefresh } from './composables/pullRefresh'
import Icon from './components/Icon.vue'

const route = useRoute()
const accountStore = useAccountStore()

const isDark = ref(false)

function applyTheme(dark: boolean) {
  isDark.value = dark
  document.documentElement.dataset.theme = dark ? 'dark' : 'light'
  localStorage.setItem('theme', dark ? 'dark' : 'light')
}

function toggleTheme() {
  applyTheme(!isDark.value)
}

onMounted(() => {
  accountStore.fetch()
  applyTheme(localStorage.getItem('theme') === 'dark')
})

const mainRef = ref<HTMLElement | null>(null)
const pullH = ref(0)
const refreshing = ref(false)
const THRESHOLD = 60
let startY = 0
let pulling = false

const tabs = [
  { path: '/', iconName: 'wallet', label: '账户' },
  { path: '/strategy', iconName: 'target', label: '策略' },
  { path: '/backtest', iconName: 'bar-chart', label: '回测' },
  { path: '/trade', iconName: 'swap', label: '交易' },
  { path: '/generator', iconName: 'search', label: '扫描' },
  { path: '/about', iconName: 'info', label: '说明' },
]

const EXTRA_TITLES: Record<string, string> = {
  '/alerts': '预警',
}

const title = computed(() => {
  const found = tabs.find((t) => t.path === route.path)
  if (found) return `A股助手 · ${found.label}`
  if (EXTRA_TITLES[route.path]) return `A股助手 · ${EXTRA_TITLES[route.path]}`
  return 'A股自动交易助手'
})

function onTouchStart(e: TouchEvent) {
  if ((mainRef.value?.scrollTop ?? 0) <= 0) {
    pulling = true
    startY = e.touches[0].clientY
  }
}

function onTouchMove(e: TouchEvent) {
  if (!pulling || refreshing.value) return
  const dy = e.touches[0].clientY - startY
  if (dy > 0) {
    pullH.value = Math.min(dy * 0.5, 100)
  }
}

async function onTouchEnd() {
  if (pulling && pullH.value >= THRESHOLD && !refreshing.value) {
    refreshing.value = true
    try {
      await triggerPullRefresh()
    } finally {
      refreshing.value = false
    }
  }
  pulling = false
  pullH.value = 0
}
</script>

<style scoped>
.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.theme-btn {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  border: 1px solid var(--border);
  background: var(--card);
  color: var(--text-2);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: color 0.15s, border-color 0.15s;
}

.theme-btn:active {
  color: var(--primary);
  border-color: var(--primary);
}
</style>
