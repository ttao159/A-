<template>
  <div class="card">
    <div class="card-title">策略收益对比</div>
    <div v-if="loading" class="empty">加载中...</div>
    <div v-else-if="!items.length" class="empty">暂无策略</div>
    <template v-else>
      <div v-for="(s, i) in items" :key="s.id" class="cmp-row">
        <div class="cmp-rank">{{ i + 1 }}</div>
        <div class="cmp-body">
          <div class="cmp-head">
            <span class="cmp-name">{{ s.name }}<span v-if="!s.enabled" class="muted">（停用）</span></span>
            <span class="cmp-pnl" :class="s.pnl >= 0 ? 'up' : 'down'">{{ fmtMoney(s.pnl) }}</span>
            <span class="cmp-ret" :class="s.return_pct >= 0 ? 'up' : 'down'">{{ fmtPct(s.return_pct) }}</span>
          </div>
          <div class="cmp-bar">
            <div class="cmp-zero"></div>
            <div class="cmp-fill" :class="s.return_pct >= 0 ? 'fill-up' : 'fill-down'" :style="barStyle(s.return_pct)"></div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { strategyApi } from '../api'
import type { StrategyCompareItem } from '../api/types'
import { fmtMoney, fmtPct } from '../utils/format'

const items = ref<StrategyCompareItem[]>([])
const loading = ref(false)

function barStyle(ret: number) {
  const maxAbs = Math.max(...items.value.map((s) => Math.abs(s.return_pct)), 0.01)
  const width = (Math.abs(ret) / maxAbs) * 50
  if (ret >= 0) return { left: '50%', width: width + '%' }
  return { left: 50 - width + '%', width: width + '%' }
}

onMounted(async () => {
  loading.value = true
  try {
    items.value = await strategyApi.compare()
  } catch (e) {
    // 对比加载失败不阻塞页面
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.cmp-row {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 10px 0;
  border-bottom: 1px dashed var(--border);
}

.cmp-row:last-child {
  border-bottom: none;
}

.cmp-rank {
  flex: 0 0 auto;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: var(--bg);
  color: var(--text-2);
  font-size: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-top: 2px;
}

.cmp-body {
  flex: 1;
  min-width: 0;
}

.cmp-head {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13px;
}

.cmp-name {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-weight: 500;
}

.cmp-pnl {
  font-variant-numeric: tabular-nums;
}

.cmp-ret {
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}

.cmp-bar {
  position: relative;
  height: 8px;
  background: var(--bg);
  border-radius: 4px;
  margin-top: 6px;
}

.cmp-zero {
  position: absolute;
  left: 50%;
  top: -2px;
  bottom: -2px;
  width: 1px;
  background: var(--border);
}

.cmp-fill {
  position: absolute;
  top: 0;
  height: 100%;
  border-radius: 4px;
}

.fill-up {
  background: #e0393e;
}

.fill-down {
  background: #1e9c4d;
}
</style>
