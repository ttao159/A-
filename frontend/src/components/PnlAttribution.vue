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
    <div v-else-if="data && data.items.length" class="attr-chips">
      <span
        v-for="item in topItems"
        :key="item.label"
        class="attr-chip"
        :class="item.pnl >= 0 ? 'up' : 'down'"
      >
        {{ item.label }} {{ item.pnl >= 0 ? '+' : '' }}{{ item.pct.toFixed(1) }}%
      </span>
      <span v-if="data.items.length > topItems.length" class="muted">等 {{ data.items.length }} 项</span>
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

const topItems = computed(() => {
  const items = data.value?.items ?? []
  const sorted = [...items].sort((a, b) => Math.abs(b.pnl) - Math.abs(a.pnl))
  return sorted.slice(0, 3)
})

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

.attr-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.attr-chip {
  font-size: 13px;
  font-weight: 600;
  padding: 2px 10px;
  border-radius: 6px;
  font-variant-numeric: tabular-nums;
}

.attr-chip.up {
  background: var(--up-bg);
  color: var(--up);
}

.attr-chip.down {
  background: var(--down-bg);
  color: var(--down);
}

.attr-empty {
  font-size: 13px;
  color: var(--text-2);
}
</style>
