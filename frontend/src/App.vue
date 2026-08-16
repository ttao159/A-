<template>
  <div class="app">
    <header class="app-header">
      <h1>{{ title }}</h1>
      <span v-if="accountStore.isLive" class="badge live">实盘</span>
      <span v-else class="badge paper">模拟盘</span>
    </header>
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
      <router-view />
    </main>
    <nav class="tab-bar">
      <router-link v-for="tab in tabs" :key="tab.path" :to="tab.path" class="tab-item">
        <span class="tab-icon">{{ tab.icon }}</span>
        <span class="tab-label">{{ tab.label }}</span>
      </router-link>
    </nav>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'
import { useAccountStore } from './stores/account'
import { triggerPullRefresh } from './composables/pullRefresh'

const route = useRoute()
const accountStore = useAccountStore()

const mainRef = ref<HTMLElement | null>(null)
const pullH = ref(0)
const refreshing = ref(false)
const THRESHOLD = 60
let startY = 0
let pulling = false

const tabs = [
  { path: '/', icon: '账', label: '账户' },
  { path: '/strategy', icon: '策', label: '策略' },
  { path: '/backtest', icon: '测', label: '回测' },
  { path: '/trade', icon: '交', label: '交易' },
  { path: '/generator', icon: '生', label: '扫描' },
]

const title = computed(() => {
  const found = tabs.find((t) => t.path === route.path)
  return found ? `A股助手 · ${found.label}` : 'A股自动交易助手'
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
