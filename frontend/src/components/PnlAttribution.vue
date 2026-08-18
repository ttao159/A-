<template>
  <div class="card attribution-card">
    <div class="row">
      <span class="card-title">今日盈亏归因</span>
      <span v-if="data" class="attr-tag">{{ data.granularity === 'industry' ? '板块' : '个股' }}</span>
    </div>
    <div v-if="loading" class="attr-empty">分析中...</div>
    <div v-else-if="error" class="attr-empty">
      {{ error }}
      <button class="retry-btn" @click="load">重试</button>
    </div>
    <div v-else-if="data && data.items.length" class="attr-bars">
      <div v-for="item in displayItems" :key="item.label" class="attr-row">
        <span class="attr-label" :title="item.label">{{ item.label }}</span>
        <div class="attr-track">
          <div class="attr-zero"></div>
          <div
            class="attr-fill"
            :class="item.pnl >= 0 ? 'pos' : 'neg'"
            :style="barStyle(item)"
          ></div>
        </div>
        <span class="attr-val" :class="item.pnl >= 0 ? 'up' : 'down'">
          {{ item.pnl >= 0 ? '+' : '' }}{{ item.pct.toFixed(1) }}%
        </span>
      </div>
      <div v-if="data.items.length > displayItems.length" class="muted attr-more">
        等 {{ data.items.length }} 项
      </div>
    </div>
    <div v-else-if="data" class="attr-empty">今日暂无持仓盈亏贡献</div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { accountApi, type PnlAttribution } from '../api'
import { useAccountStore } from '../stores/account'
import { netStatus } from '../composables/netStatus'

const accountStore = useAccountStore()

const loading = ref(false)
const error = ref('')
const data = ref<PnlAttribution | null>(null)

const displayItems = computed(() => {
  const items = data.value?.items ?? []
  return [...items].sort((a, b) => Math.abs(b.pnl) - Math.abs(a.pnl)).slice(0, 5)
})

const maxAbs = computed(() =>
  Math.max(...displayItems.value.map((i) => Math.abs(i.pnl)), 1e-9),
)

function barStyle(item: { pnl: number }) {
  const w = (Math.abs(item.pnl) / maxAbs.value) * 50
  if (item.pnl >= 0) return { left: '50%', width: `${w}%` }
  return { left: `${50 - w}%`, width: `${w}%` }
}

let inFlight = false

async function load() {
  if (inFlight) return
  inFlight = true
  loading.value = true
  error.value = ''
  try {
    data.value = await accountApi.attribution()
  } catch (e) {
    error.value = '归因加载失败'
  } finally {
    loading.value = false
    inFlight = false
  }
}

onMounted(load)

watch(
  () => accountStore.account?.total_pnl,
  () => {
    if (netStatus.online) load()
  },
)

watch(
  () => netStatus.online,
  (on) => {
    if (on) load()
  },
)
</script>

<style scoped>
.attr-tag {
  font-size: 11px;
  font-weight: 600;
  color: var(--text-2);
  background: var(--bg);
  padding: 1px 6px;
  border-radius: 4px;
}

.attr-bars {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.attr-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.attr-label {
  flex: 0 0 64px;
  min-width: 0;
  font-size: 12px;
  color: var(--text-2);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.attr-track {
  position: relative;
  flex: 1;
  height: 14px;
  background: var(--bg);
  border-radius: 7px;
  overflow: hidden;
}

.attr-zero {
  position: absolute;
  left: 50%;
  top: 0;
  bottom: 0;
  width: 1px;
  background: var(--border);
}

.attr-fill {
  position: absolute;
  top: 0;
  height: 100%;
  border-radius: 7px;
  transition: width 0.3s ease, left 0.3s ease;
}

.attr-fill.pos {
  background: var(--up);
}

.attr-fill.neg {
  background: var(--down);
}

.attr-val {
  flex: 0 0 58px;
  text-align: right;
  font-size: 12px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}

.attr-more {
  font-size: 12px;
}

.attr-empty {
  font-size: 13px;
  color: var(--text-2);
}
</style>
