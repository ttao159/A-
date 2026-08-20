<template>
  <div class="app">
    <header class="app-header">
      <h1>{{ title }}</h1>
      <div class="header-right">
        <button class="theme-btn" @click="toggleTheme" aria-label="切换主题">
          <Icon :name="isDark ? 'sun' : 'moon'" :size="18" />
        </button>
        <select
          class="mode-select"
          :value="accountStore.isLive ? 'live' : 'paper'"
          aria-label="交易模式"
          title="实盘(Demo): 随机/历史回放数据模拟，非真实券商行情"
          @change="onModeChange"
        >
          <option value="paper">模拟盘</option>
          <option value="live">实盘 (Demo)</option>
        </select>
        <button class="logout-btn" @click="handleLogout" aria-label="退出登录">
          <Icon name="log-out" :size="18" />
        </button>
      </div>
    </header>
    <div v-if="userStore.isDemo" class="demo-banner">
      Demo 只读模式：数据为随机/历史回放，仅供策略体验，无法下单或修改策略
    </div>
    <div v-if="accountStore.isLive" class="risk-banner">
      实盘交易存在风险，请谨慎操作并核实每笔委托
    </div>
    <div v-if="!netStatus.online" class="net-banner">
      网络连接中断，正在自动重连...
    </div>
    <div class="ptr-indicator" :style="{ height: pullH + 'px' }">
      <template v-if="refreshing">
        <span class="ptr-spinner"></span>
        <span>刷新中...</span>
      </template>
      <template v-else-if="pullH >= THRESHOLD">
        <span class="ptr-arrow">↓</span>
        <span>释放刷新</span>
      </template>
      <template v-else>
        <span class="ptr-arrow" :style="{ transform: `rotate(${Math.min(pullH / THRESHOLD, 1) * 180}deg)` }">↓</span>
        <span>下拉刷新</span>
      </template>
    </div>
    <main
      ref="mainRef"
      class="app-main"
      @touchstart="onTouchStart"
      @touchmove="onTouchMove"
      @touchend="onTouchEnd"
      @scroll="onMainScroll"
    >
      <router-view v-slot="{ Component }">
        <Transition name="page" mode="out-in">
          <component :is="Component" />
        </Transition>
      </router-view>
    </main>
    <Transition name="fab-pop">
      <button v-if="showTopBtn" class="top-btn" aria-label="回到顶部" @click="scrollToTop">
        <Icon name="chevron-up" :size="22" />
      </button>
    </Transition>
    <nav class="tab-bar">
      <router-link
        v-for="tab in tabs"
        :key="tab.path"
        :to="tab.path"
        class="tab-item"
        :class="{ 'router-link-active': tab.exact ? route.path === tab.path : route.path.startsWith(tab.path) }"
      >
        <Icon :name="tab.iconName" :size="22" />
        <span class="tab-label">{{ tab.label }}</span>
      </router-link>
    </nav>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAccountStore } from './stores/account'
import { useUserStore } from './stores/user'
import { triggerPullRefresh } from './composables/pullRefresh'
import { netStatus } from './composables/netStatus'
import { toast } from './utils/toast'
import { confirmDialog } from './utils/confirm'
import Icon from './components/Icon.vue'

const route = useRoute()
const router = useRouter()
const accountStore = useAccountStore()
const userStore = useUserStore()

function handleLogout() {
  userStore.logout()
  router.push('/login')
}

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
const showTopBtn = ref(false)
const THRESHOLD = 60
let startY = 0
let pulling = false

function onMainScroll() {
  showTopBtn.value = (mainRef.value?.scrollTop ?? 0) > 300
}

function scrollToTop() {
  mainRef.value?.scrollTo({ top: 0, behavior: 'smooth' })
}

const tabs = [
  { path: '/', iconName: 'wallet', label: '账户', exact: true },
  { path: '/trade', iconName: 'swap', label: '交易' },
  { path: '/strategy', iconName: 'target', label: '策略中心' },
  { path: '/about', iconName: 'info', label: '说明' },
]

const title = computed(() => {
  const t = route.meta.title as string | undefined
  if (t) return `A股助手 · ${t}`
  return 'A股自动交易助手'
})

async function onModeChange(e: Event) {
  const sel = e.target as HTMLSelectElement
  if (sel.value === 'live' && !accountStore.isLive) {
    sel.value = 'paper'
    const ok = await confirmDialog({
      title: '实盘模式 (Demo)',
      message: '当前实盘为演示版本，使用随机/历史回放行情数据，非真实券商通道。\n\n切换后策略将基于模拟数据进行决策，与实际市场存在偏差。\n\n确认切换？',
      confirmText: '确认切换',
      danger: true,
    })
    if (ok) {
      sel.value = 'live'
      accountStore.setLive(true)
      toast('已切换至实盘演示模式')
    }
  } else if (sel.value === 'paper' && accountStore.isLive) {
    accountStore.setLive(false)
    toast('已切换至模拟盘')
  }
}

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
      toast('刷新成功')
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

.mode-select {
  height: 34px;
  padding: 0 8px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--card);
  color: var(--text);
  font-size: 13px;
  font-weight: 600;
  outline: none;
  cursor: pointer;
}

.mode-select option {
  background: var(--card);
  color: var(--text);
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
  transform: scale(0.92);
}

.logout-btn {
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
}

.logout-btn:active {
  color: var(--danger);
  border-color: var(--danger);
  transform: scale(0.92);
}

.ptr-arrow {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  margin-right: 6px;
  transition: transform 0.2s;
}

.net-banner {
  padding: 8px 16px;
  background: var(--warning-bg);
  color: var(--warning);
  font-size: 13px;
  text-align: center;
  border-bottom: 1px solid var(--border);
}

.demo-banner {
  padding: 8px 16px;
  background: var(--border-light);
  color: var(--text-2);
  font-size: 12px;
  text-align: center;
  border-bottom: 1px solid var(--border);
  line-height: 1.5;
}

.ptr-spinner {
  width: 14px;
  height: 14px;
  border: 2px solid var(--border);
  border-top-color: var(--primary);
  border-radius: 50%;
  animation: ptr-spin 0.8s linear infinite;
  margin-right: 6px;
}

.top-btn {
  position: fixed;
  right: 16px;
  bottom: calc(76px + env(safe-area-inset-bottom));
  z-index: 24;
  width: 42px;
  height: 42px;
  border-radius: 50%;
  border: 1px solid var(--border);
  background: var(--card);
  color: var(--text-2);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.18);
  cursor: pointer;
  transition: color 0.15s, border-color 0.15s;
  -webkit-tap-highlight-color: transparent;
}

.top-btn:active {
  color: var(--primary);
  border-color: var(--primary);
  transform: scale(0.92);
}

.fab-pop-enter-active,
.fab-pop-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.fab-pop-enter-from,
.fab-pop-leave-to {
  opacity: 0;
  transform: translateY(10px);
}

@keyframes ptr-spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
